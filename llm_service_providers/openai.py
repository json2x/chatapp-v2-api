import os
from typing import Dict, List, Any, Generator, Optional, Union

import openai
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OpenAIChat:
    """
    A class for interacting with OpenAI's chat completion API with streaming support.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAIChat class.
        
        Args:
            api_key: Optional API key for OpenAI. If not provided, it will be read from the environment variable OPENAI_API_KEY.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def stream_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[ChatCompletionChunk, None, None]:
        """
        Stream a chat completion from OpenAI.
        
        Args:
            model: The OpenAI model to use (e.g., "gpt-4o", "gpt-4", "gpt-3.5-turbo")
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API (temperature, top_p, n, etc.)
            
        Returns:
            A generator that yields ChatCompletionChunk objects as they are received
        
        Example:
            ```python
            openai_chat = OpenAIChat()
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me a joke."}
            ]
            
            for chunk in openai_chat.stream_chat_completion(
                model="gpt-4", 
                messages=messages,
                temperature=0.7
            ):
                # Process each chunk
                print(chunk.choices[0].delta.content or "", end="")
            ```
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,  # Enable streaming
            **kwargs  # Pass through any additional parameters
        )
    
    def get_full_completion_from_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Get the full completion text from a streaming response.
        
        Args:
            model: The OpenAI model to use
            messages: A list of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the chat completion API
            
        Returns:
            The complete response text
        """
        full_response = ""
        for chunk in self.stream_chat_completion(model, messages, **kwargs):
            content = chunk.choices[0].delta.content
            if content is not None:
                full_response += content
        
        return full_response