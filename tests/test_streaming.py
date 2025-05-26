import os
import unittest
from unittest.mock import patch, MagicMock
import sys
from typing import Dict, List, Any, Generator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service_providers.openai import OpenAIChat
from llm_service_providers.anthropic import AnthropicChat


class TestOpenAIStreaming(unittest.TestCase):
    """Test cases for OpenAI streaming functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Skip tests if API key is not available
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
        
        self.openai_chat = OpenAIChat(api_key=self.api_key)
        self.test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'hello world' and nothing else."}
        ]
    
    def test_stream_chat_completion_real(self):
        """Test streaming chat completion with real API call."""
        # This test will only run if OPENAI_API_KEY is set and RUN_REAL_API_TESTS=1
        if not os.getenv("RUN_REAL_API_TESTS"):
            self.skipTest("Skipping real API test. Set RUN_REAL_API_TESTS=1 to run.")
        
        # Test with a simple prompt
        chunks = list(self.openai_chat.stream_chat_completion(
            model="gpt-3.5-turbo",
            messages=self.test_messages,
            temperature=0,
            max_tokens=10
        ))
        
        # Verify we got some chunks back
        self.assertTrue(len(chunks) > 0)
        
        # Verify the chunks have the expected structure
        for chunk in chunks:
            self.assertTrue(hasattr(chunk, 'choices'))
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                # We found a content chunk
                self.assertIsInstance(chunk.choices[0].delta.content, str)
    
    def test_get_full_completion_from_stream_real(self):
        """Test getting full completion from stream with real API call."""
        if not os.getenv("RUN_REAL_API_TESTS"):
            self.skipTest("Skipping real API test. Set RUN_REAL_API_TESTS=1 to run.")
        
        # Get the full response
        response = self.openai_chat.get_full_completion_from_stream(
            model="gpt-3.5-turbo",
            messages=self.test_messages,
            temperature=0,
            max_tokens=10
        )
        
        # Verify we got a non-empty string response
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    @patch('openai.OpenAI')
    def test_stream_chat_completion_mock(self, mock_openai):
        """Test streaming chat completion with mocked API."""
        # Create a mock for the streaming response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create mock chunks
        mock_delta1 = MagicMock()
        mock_delta1.content = "Hello"
        mock_choice1 = MagicMock()
        mock_choice1.delta = mock_delta1
        
        mock_delta2 = MagicMock()
        mock_delta2.content = " world"
        mock_choice2 = MagicMock()
        mock_choice2.delta = mock_delta2
        
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [mock_choice1]
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [mock_choice2]
        
        # Set up the mock to return our fake chunks
        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]
        
        # Create a new instance with the mocked client
        openai_chat = OpenAIChat(api_key="fake_key")
        
        # Call the method
        chunks = list(openai_chat.stream_chat_completion(
            model="gpt-3.5-turbo",
            messages=self.test_messages
        ))
        
        # Verify the method was called with the right parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=self.test_messages,
            stream=True
        )
        
        # Verify we got our mock chunks back
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].choices[0].delta.content, "Hello")
        self.assertEqual(chunks[1].choices[0].delta.content, " world")
    
    @patch('openai.OpenAI')
    def test_get_full_completion_from_stream_mock(self, mock_openai):
        """Test getting full completion from stream with mocked API."""
        # Create a mock for the streaming response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create mock chunks
        mock_delta1 = MagicMock()
        mock_delta1.content = "Hello"
        mock_choice1 = MagicMock()
        mock_choice1.delta = mock_delta1
        
        mock_delta2 = MagicMock()
        mock_delta2.content = " world"
        mock_choice2 = MagicMock()
        mock_choice2.delta = mock_delta2
        
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [mock_choice1]
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [mock_choice2]
        
        # Set up the mock to return our fake chunks
        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]
        
        # Create a new instance with the mocked client
        openai_chat = OpenAIChat(api_key="fake_key")
        
        # Call the method
        response = openai_chat.get_full_completion_from_stream(
            model="gpt-3.5-turbo",
            messages=self.test_messages
        )
        
        # Verify we got the expected response
        self.assertEqual(response, "Hello world")


class TestAnthropicStreaming(unittest.TestCase):
    """Test cases for Anthropic streaming functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Skip tests if API key is not available
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.skipTest("ANTHROPIC_API_KEY environment variable not set")
        
        self.anthropic_chat = AnthropicChat(api_key=self.api_key)
        self.test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'hello world' and nothing else."}
        ]
    
    def test_stream_chat_completion_real(self):
        """Test streaming chat completion with real API call."""
        # This test will only run if ANTHROPIC_API_KEY is set and RUN_REAL_API_TESTS=1
        if not os.getenv("RUN_REAL_API_TESTS"):
            self.skipTest("Skipping real API test. Set RUN_REAL_API_TESTS=1 to run.")
        
        # Test with a simple prompt
        events = list(self.anthropic_chat.stream_chat_completion(
            model="claude-3-haiku-20240307",
            messages=self.test_messages,
            temperature=0,
            max_tokens=10
        ))
        
        # Verify we got some events back
        self.assertTrue(len(events) > 0)
        
        # Verify at least one content_block_delta event
        content_events = [e for e in events if e.type == "content_block_delta"]
        self.assertTrue(len(content_events) > 0)
        
        # Check that we have text in at least one event
        has_text = False
        for event in content_events:
            if hasattr(event.delta, 'text') and event.delta.text:
                has_text = True
                break
        self.assertTrue(has_text)
    
    def test_get_full_completion_from_stream_real(self):
        """Test getting full completion from stream with real API call."""
        if not os.getenv("RUN_REAL_API_TESTS"):
            self.skipTest("Skipping real API test. Set RUN_REAL_API_TESTS=1 to run.")
        
        # Get the full response
        response = self.anthropic_chat.get_full_completion_from_stream(
            model="claude-3-haiku-20240307",
            messages=self.test_messages,
            temperature=0,
            max_tokens=10
        )
        
        # Verify we got a non-empty string response
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    @patch('anthropic.Anthropic')
    def test_stream_chat_completion_mock(self, mock_anthropic):
        """Test streaming chat completion with mocked API."""
        # Create a mock for the streaming response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Create mock events
        mock_delta1 = MagicMock()
        mock_delta1.text = "Hello"
        mock_event1 = MagicMock()
        mock_event1.type = "content_block_delta"
        mock_event1.delta = mock_delta1
        
        mock_delta2 = MagicMock()
        mock_delta2.text = " world"
        mock_event2 = MagicMock()
        mock_event2.type = "content_block_delta"
        mock_event2.delta = mock_delta2
        
        # Set up the mock to return our fake events
        mock_client.messages.stream.return_value = [mock_event1, mock_event2]
        
        # Create a new instance with the mocked client
        anthropic_chat = AnthropicChat(api_key="fake_key")
        
        # Call the method
        events = list(anthropic_chat.stream_chat_completion(
            model="claude-3-opus-20240229",
            messages=self.test_messages
        ))
        
        # Verify we got our mock events back
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].delta.text, "Hello")
        self.assertEqual(events[1].delta.text, " world")
    
    @patch('anthropic.Anthropic')
    def test_get_full_completion_from_stream_mock(self, mock_anthropic):
        """Test getting full completion from stream with mocked API."""
        # Create a mock for the streaming response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Create mock events
        mock_delta1 = MagicMock()
        mock_delta1.text = "Hello"
        mock_event1 = MagicMock()
        mock_event1.type = "content_block_delta"
        mock_event1.delta = mock_delta1
        
        mock_delta2 = MagicMock()
        mock_delta2.text = " world"
        mock_event2 = MagicMock()
        mock_event2.type = "content_block_delta"
        mock_event2.delta = mock_delta2
        
        # Set up the mock to return our fake events
        mock_client.messages.stream.return_value = [mock_event1, mock_event2]
        
        # Create a new instance with the mocked client
        anthropic_chat = AnthropicChat(api_key="fake_key")
        
        # Call the method
        response = anthropic_chat.get_full_completion_from_stream(
            model="claude-3-opus-20240229",
            messages=self.test_messages
        )
        
        # Verify we got the expected response
        self.assertEqual(response, "Hello world")


if __name__ == '__main__':
    unittest.main()
