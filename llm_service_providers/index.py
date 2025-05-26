"""
LLM Service Provider Wrapper

This module provides a unified interface for interacting with different LLM service providers.
It automatically selects the appropriate provider based on the requested model.
"""

import os
from typing import Dict, List, Any, Generator, Optional, Union
from dotenv import load_dotenv

from .openai import OpenAIChat
from .anthropic import AnthropicChat
from misc.constants import Provider, MODEL_PROVIDER_MAP, DEFAULT_MODELS, CONVERSATION_MESSAGES_THRESHOLD
from misc.db import get_conversation

# Load environment variables from .env file
load_dotenv()


class LLMServiceProvider:
    """
    A unified interface for interacting with different LLM service providers.
    This class automatically selects the appropriate provider based on the requested model.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """
        Initialize the LLM service provider wrapper.
        
        Args:
            openai_api_key: Optional API key for OpenAI. If not provided, it will be read from the environment variable.
            anthropic_api_key: Optional API key for Anthropic. If not provided, it will be read from the environment variable.
        """
        self.providers = {}
        
        # Initialize OpenAI provider if API key is available
        try:
            self.providers[Provider.OPENAI] = OpenAIChat(api_key=openai_api_key)
        except ValueError as e:
            print(f"Warning: OpenAI provider not initialized: {e}")
        
        # Initialize Anthropic provider if API key is available
        try:
            self.providers[Provider.ANTHROPIC] = AnthropicChat(api_key=anthropic_api_key)
        except ValueError as e:
            print(f"Warning: Anthropic provider not initialized: {e}")
    
    def get_provider_for_model(self, model: str) -> str:
        """
        Get the appropriate provider for the given model.
        
        Args:
            model: The model name
            
        Returns:
            The provider name
            
        Raises:
            ValueError: If the model is not supported
        """
        if model in MODEL_PROVIDER_MAP:
            return MODEL_PROVIDER_MAP[model]
        
        # Try to infer provider from model name prefix
        if model.startswith("gpt-") or model.startswith("text-"):
            return Provider.OPENAI
        elif model.startswith("claude-"):
            return Provider.ANTHROPIC
        
        raise ValueError(f"Unsupported model: {model}. Available models: {list(MODEL_PROVIDER_MAP.keys())}")
    
    def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[Any, None, None]:
        """
        Stream a chat completion from the appropriate provider based on the model.
        
        Args:
            model: The model to use (e.g., "gpt-4o", "claude-3-5-haiku-20241022")
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API
            
        Returns:
            A generator that yields response chunks as they are received
            
        Raises:
            ValueError: If the model is not supported or the provider is not initialized
        """
        provider_name = self.get_provider_for_model(model)
        
        if provider_name not in self.providers:
            available_providers = list(self.providers.keys())
            raise ValueError(
                f"Provider {provider_name} is not initialized. "
                f"Available providers: {available_providers}. "
                f"Please provide a valid API key for {provider_name}."
            )
        
        provider = self.providers[provider_name]
        return provider.stream_chat_completion(model=model, messages=messages, **kwargs)
    
    def get_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Get a complete chat completion from the appropriate provider based on the model.
        
        Args:
            model: The model to use (e.g., "gpt-4o", "claude-3-5-haiku-20241022")
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API
            
        Returns:
            The complete response text
            
        Raises:
            ValueError: If the model is not supported or the provider is not initialized
        """
        provider_name = self.get_provider_for_model(model)
        
        if provider_name not in self.providers:
            available_providers = list(self.providers.keys())
            raise ValueError(
                f"Provider {provider_name} is not initialized. "
                f"Available providers: {available_providers}. "
                f"Please provide a valid API key for {provider_name}."
            )
        
        provider = self.providers[provider_name]
        return provider.get_full_completion_from_stream(model=model, messages=messages, **kwargs)
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get a dictionary of available models grouped by provider.
        
        Returns:
            A dictionary where keys are provider names and values are lists of model names
        """
        available_models = {}
        
        for provider_name in self.providers:
            available_models[provider_name] = [
                model for model, provider in MODEL_PROVIDER_MAP.items()
                if provider == provider_name
            ]
        
        return available_models
        
    def get_message_history(self, conversation_id: str, summarize: bool = True) -> List[Dict[str, str]]:
        """
        Fetch messages for a conversation and handle summarization for long conversations.
        
        This function retrieves all messages for a given conversation_id from the database.
        If the number of messages exceeds CONVERSATION_MESSAGES_THRESHOLD and summarize is True, it will:
        1. Keep the most recent messages up to the threshold
        2. Summarize the older messages
        3. Add the summary as a system message at the beginning
        
        Args:
            conversation_id: The ID of the conversation to fetch messages for
            summarize: Whether to summarize older messages if they exceed the threshold (default: True)
            
        Returns:
            A list of message dictionaries with 'role' and 'content' keys,
            potentially including a summary of older messages as a system message
            
        Raises:
            ValueError: If the conversation is not found
        """
        # Fetch the conversation from the database
        conversation = get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        # Extract messages from the conversation
        db_messages = conversation.get('messages', [])
        
        # Convert database messages to the format expected by LLM providers
        messages = []
        for msg in db_messages:
            # Skip messages with invalid roles
            if msg['role'] not in ['user', 'assistant', 'system']:
                continue
                
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        # If messages don't exceed threshold, return as is
        if len(messages) <= CONVERSATION_MESSAGES_THRESHOLD:
            return messages
        
        # If summarize is False, return all messages without summarization
        if not summarize:
            return messages
        
        # Split messages: keep recent ones and summarize older ones
        recent_messages = messages[-CONVERSATION_MESSAGES_THRESHOLD:]
        older_messages = messages[:-CONVERSATION_MESSAGES_THRESHOLD]
        
        # Only summarize if there are older messages
        if older_messages:
            try:
                # Generate a summary of the older messages
                summary = self.brief_summary_of_conversation_history(older_messages)
                
                # Add the summary as a system message at the beginning
                summary_message = {
                    'role': 'system',
                    'content': f"Summary of previous conversation: \n{summary}"
                }
                
                # Return the summary followed by recent messages
                return [summary_message] + recent_messages
            except Exception as e:
                # If summarization fails, log the error and return just the recent messages
                print(f"Error summarizing conversation history: {e}")
                return recent_messages
        
        # If we somehow got here, return the recent messages
        return recent_messages
    
    def brief_summary_of_conversation_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a brief summary of the conversation history in bullet points.
        Always uses the gpt-4o-mini model for consistent results.
        
        Args:
            messages: A list of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens for the summary
            temperature: Temperature for generation (lower = more deterministic)
            
        Returns:
            A string containing the summary of the conversation in bullet points
            
        Raises:
            ValueError: If OpenAI provider is not initialized
        """
        # Check if OpenAI provider is available
        if Provider.OPENAI not in self.providers:
            raise ValueError("OpenAI provider is not initialized. Please provide a valid OpenAI API key.")
        
        # Always use gpt-4o-mini model for summarization
        model = "gpt-4o-mini"
        provider_name = Provider.OPENAI
        
        # Process messages to replace image/attachment references with <resource /> tag
        processed_messages = []
        for msg in messages:
            # Create a copy of the message to avoid modifying the original
            processed_msg = msg.copy()
            
            # Check if content contains image/attachment references and replace them
            if "content" in processed_msg and processed_msg["content"]:
                # Replace image markdown format ![alt](url)
                import re
                processed_msg["content"] = re.sub(r'!\[.*?\]\(.*?\)', '<resource />', processed_msg["content"])
                
                # Replace HTML image tags
                processed_msg["content"] = re.sub(r'<img[^>]*>', '<resource />', processed_msg["content"])
                
                # Replace base64 encoded images
                processed_msg["content"] = re.sub(r'data:image\/[^;]+;base64,[^\"\s]+', '<resource />', processed_msg["content"])
                
                # Replace attachment references (assuming a specific format, adjust as needed)
                processed_msg["content"] = re.sub(r'\[attachment:.*?\]', '<resource />', processed_msg["content"])
            
            processed_messages.append(processed_msg)
        
        # Create a system message instructing the model to create a summary
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversations. "
                      "Create a concise summary of the following conversation in bullet points. "
                      "Focus on the main topics, questions, and answers. "
                      "Be factual and objective. Do not add information not present in the conversation. "
                      "Format your response as a list of bullet points using the '- ' prefix."
        }
        
        # Create a user message with the instruction
        user_message = {
            "role": "user",
            "content": "Please summarize the following conversation in bullet points:\n\n"
                      + "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in processed_messages])
        }
        
        # Generate the summary
        summary = self.get_chat_completion(
            model=model,
            messages=[system_message, user_message],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return summary


# Create a singleton instance for easy import
llm_service = LLMServiceProvider()
