import os
from typing import Dict, List, Any, Generator, Optional, Union

import anthropic
from anthropic.types import Message, MessageParam, MessageStreamEvent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AnthropicChat:
    """
    A class for interacting with Anthropic's chat completion API with streaming support.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AnthropicChat class.
        
        Args:
            api_key: Optional API key for Anthropic. If not provided, it will be read from the environment variable ANTHROPIC_API_KEY.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def stream_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[MessageStreamEvent, None, None]:
        """
        Stream a chat completion from Anthropic.
        
        Args:
            model: The Anthropic model to use (e.g., "claude-3-opus-20240229", "claude-3-sonnet-20240229")
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API (temperature, top_p, max_tokens, etc.)
            
        Returns:
            A generator that yields MessageStreamEvent objects as they are received
        
        Example:
            ```python
            anthropic_chat = AnthropicChat()
            messages = [
                {"role": "user", "content": "Tell me a joke."}
            ]
            
            for event in anthropic_chat.stream_chat_completion(
                model="claude-3-opus-20240229", 
                messages=messages,
                temperature=0.7
            ):
                if event.type == "content_block_delta":
                    print(event.delta.text, end="")
            ```
        """
        # Convert messages to Anthropic's format
        anthropic_messages = []
        for msg in messages:
            role = msg["role"]
            # Map OpenAI roles to Anthropic roles if needed
            if role == "system":
                # Handle system message separately as it's not a regular message in Anthropic
                system_prompt = msg["content"]
                kwargs["system"] = system_prompt
                continue
            elif role == "assistant":
                anthropic_role = "assistant"
            elif role == "user":
                anthropic_role = "user"
            else:
                # Skip unsupported roles
                continue
                
            anthropic_messages.append({"role": anthropic_role, "content": msg["content"]})
        
        # Get the stream manager
        stream_manager = self.client.messages.stream(
            model=model,
            messages=anthropic_messages,
            **kwargs
        )
        
        # Handle both context manager and list return types (for testing)
        try:
            # Try to use it as a context manager (normal operation)
            with stream_manager as stream:
                for event in stream:
                    yield event
        except (AttributeError, TypeError):
            # If it's not a context manager (in tests), treat it as an iterable
            for event in stream_manager:
                yield event
    
    def get_full_completion_from_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Get the full completion text from a streaming response.
        
        Args:
            model: The Anthropic model to use
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API
            
        Returns:
            The complete response text
        """
        full_response = ""
        for event in self.stream_chat_completion(model, messages, **kwargs):
            if event.type == "content_block_delta":
                full_response += event.delta.text
        
        return full_response