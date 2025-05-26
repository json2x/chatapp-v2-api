import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import uuid
from typing import Dict, List, Any, Generator
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app
from routes.chat import ChatRequest
from llm_service_providers.index import LLMServiceProvider


class TestChatEndpoint(unittest.TestCase):
    """Test cases for the chat endpoint."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        
        # Create a mock for the LLM service
        self.llm_service_patcher = patch('routes.chat.llm_service')
        self.mock_llm_service = self.llm_service_patcher.start()
        
        # Create a mock for the database functions
        self.create_conversation_patcher = patch('routes.chat.create_conversation')
        self.mock_create_conversation = self.create_conversation_patcher.start()
        
        self.add_message_patcher = patch('routes.chat.add_message')
        self.mock_add_message = self.add_message_patcher.start()
        
        self.get_conversation_patcher = patch('routes.chat.get_conversation')
        self.mock_get_conversation = self.get_conversation_patcher.start()
        
        # Set up default return values
        self.conversation_id = str(uuid.uuid4())
        self.mock_create_conversation.return_value = self.conversation_id
        
        # Mock the get_available_models method
        self.mock_llm_service.get_available_models.return_value = {
            "openai": ["gpt-4o-mini", "gpt-4o"],
            "anthropic": ["claude-3-5-haiku-20241022"]
        }
        
        # Mock the get_message_history method
        self.mock_llm_service.get_message_history.return_value = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Create a generator for stream_chat mock
        def mock_stream():
            # Mock OpenAI response format
            for text in ["Hello", ", ", "I'm ", "an ", "AI ", "assistant", "."]:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta = MagicMock()
                mock_chunk.choices[0].delta.content = text
                yield mock_chunk
        
        # Set the mock for stream_chat
        self.mock_llm_service.stream_chat.return_value = mock_stream()
    
    def tearDown(self):
        """Clean up after tests."""
        self.llm_service_patcher.stop()
        self.create_conversation_patcher.stop()
        self.add_message_patcher.stop()
        self.get_conversation_patcher.stop()
    
    def test_chat_new_conversation(self):
        """Test creating a new chat conversation."""
        # Make a request to the chat endpoint
        response = self.client.post(
            "/api/chat",
            json={
                "model": "gpt-4o-mini",
                "message": "Hello, how are you?"
            }
        )
        
        # Check that the response is a streaming response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/event-stream; charset=utf-8")
        
        # Parse the streamed response
        content = ""
        conversation_id = None
        
        for line in response.iter_lines():
            if line:
                # Skip empty lines
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    content += data.get("content", "")
                    if data.get("done", False):
                        conversation_id = data.get("conversation_id")
        
        # Check that we got the expected content and conversation ID
        self.assertEqual(content, "Hello, I'm an AI assistant.")
        self.assertEqual(conversation_id, self.conversation_id)
        
        # Verify that create_conversation was called
        self.mock_create_conversation.assert_called_once_with(
            title="Hello, how are you?",
            model="gpt-4o-mini",
            system_prompt=None
        )
        
        # Verify that add_message was called for the user message
        self.mock_add_message.assert_any_call(
            conversation_id=self.conversation_id,
            role="user",
            content="Hello, how are you?"
        )
        
        # Verify that get_message_history was called
        self.mock_llm_service.get_message_history.assert_called_once_with(
            conversation_id=self.conversation_id,
            summarize=True
        )
        
        # Verify that stream_chat was called with the right parameters
        self.mock_llm_service.stream_chat.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, how are you?"}]
        )
    
    def test_chat_existing_conversation(self):
        """Test adding to an existing chat conversation."""
        # Make a request to the chat endpoint with an existing conversation ID
        response = self.client.post(
            "/api/chat",
            json={
                "model": "gpt-4o-mini",
                "message": "What's the weather like?",
                "conversation_session_id": self.conversation_id,
                "summarize_history": False
            }
        )
        
        # Check that the response is a streaming response
        self.assertEqual(response.status_code, 200)
        
        # Verify that create_conversation was NOT called
        self.mock_create_conversation.assert_not_called()
        
        # Verify that add_message was called for the user message
        self.mock_add_message.assert_any_call(
            conversation_id=self.conversation_id,
            role="user",
            content="What's the weather like?"
        )
        
        # Verify that get_message_history was called with summarize=False
        self.mock_llm_service.get_message_history.assert_called_once_with(
            conversation_id=self.conversation_id,
            summarize=False
        )
    
    def test_chat_invalid_model(self):
        """Test requesting chat with an invalid model."""
        # Make a request with an invalid model
        response = self.client.post(
            "/api/chat",
            json={
                "model": "nonexistent-model",
                "message": "Hello"
            }
        )
        
        # Check that we get a 400 error
        self.assertEqual(response.status_code, 400)
        self.assertIn("not available", response.json()["detail"])
    
    @patch('routes.chat.stream_generator')
    def test_chat_exception_handling(self, mock_stream_generator):
        """Test handling of exceptions during streaming."""
        # Set up the mock to raise an exception
        async def mock_generator(*args, **kwargs):
            yield "data: {\"error\": \"Test error\", \"done\": true}\n\n"
        
        mock_stream_generator.return_value = mock_generator()
        
        # Make a request to the chat endpoint
        response = self.client.post(
            "/api/chat",
            json={
                "model": "gpt-4o-mini",
                "message": "Hello"
            }
        )
        
        # Check that we still get a 200 response (error is in the stream)
        self.assertEqual(response.status_code, 200)
        
        # Parse the streamed response to check for the error
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    if data.get("error"):
                        self.assertEqual(data["error"], "Test error")


if __name__ == '__main__':
    unittest.main()
