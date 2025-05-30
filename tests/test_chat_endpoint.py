"""
Tests for the chat API endpoint.

This module tests the following endpoint:
- POST /api/chat
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import uuid
from tests.test_base import BaseTest
from database.crud import create_conversation, add_message, get_message_history
from schema.chat import ChatRequest


class TestChatEndpoint(BaseTest):
    """Test the chat API endpoint."""
    
    def setUp(self):
        """Set up before each test."""
        super().setUp()
        self.mock_llm_service()
        
        # Create a sample chat request
        self.chat_request = {
            "model": "gpt-4o-mini",
            "message": "Hello, how are you?",
            "system_prompt": "You are a helpful assistant."
        }
        
        # Create a sample conversation
        self.conversation_id = str(uuid.uuid4())
        self.mock_conversation = self.create_mock_conversation_dict()
        self.mock_conversation['id'] = self.conversation_id
        
        # Mock the message history
        self.mock_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
    
    def test_chat_new_conversation(self):
        """Test the POST /api/chat endpoint with a new conversation."""
        # Create a mock conversation dictionary
        mock_conversation = self.create_mock_conversation_dict()
        
        # Mock the create_conversation, add_message, and get_message_history functions
        with patch("routes.chat.create_conversation", return_value=mock_conversation), \
            patch("routes.chat.add_message", return_value={}), \
            patch("routes.chat.get_message_history", return_value=self.mock_messages):
            
            # Make the request
            response = self.client.post("/api/chat", json=self.chat_request)
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            # Content type might include charset, so check if it starts with text/event-stream
            self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
    
    def test_chat_existing_conversation(self):
        """Test the POST /api/chat endpoint with an existing conversation."""
        # Update the chat request to include a conversation ID
        chat_request_with_id = self.chat_request.copy()
        chat_request_with_id["conversation_session_id"] = self.conversation_id
        
        # Mock the add_message and get_message_history functions
        with patch("routes.chat.add_message", return_value=MagicMock()), \
             patch("routes.chat.get_message_history", return_value=self.mock_messages):
            
            # Make the request
            response = self.client.post("/api/chat", json=chat_request_with_id)
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            # Content type might include charset, so check if it starts with text/event-stream
            self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
    
    def test_chat_invalid_model(self):
        """Test the POST /api/chat endpoint with an invalid model."""
        # Update the chat request to include an invalid model
        invalid_model_request = self.chat_request.copy()
        invalid_model_request["model"] = "invalid-model"
        
        # Mock the get_available_models method to return no models
        with patch("routes.chat.llm_service.get_available_models", 
                  return_value={"openai": ["gpt-4o-mini"]}):
            
            
            # Make the request
            response = self.client.post("/api/chat", json=invalid_model_request)
            
            # Check the response
            self.assertEqual(response.status_code, 400)
            self.assertIn("not available", response.json()["detail"])
    
    def test_chat_with_summarize_history_false(self):
        """Test the POST /api/chat endpoint with summarize_history=False."""
        # Update the chat request to disable history summarization
        no_summarize_request = self.chat_request.copy()
        no_summarize_request["summarize_history"] = False
        no_summarize_request["conversation_session_id"] = self.conversation_id
        
        # Mock the add_message and get_message_history functions
        with patch("routes.chat.add_message", return_value=MagicMock()), \
             patch("routes.chat.get_message_history", return_value=self.mock_messages):
            
            # Make the request
            response = self.client.post("/api/chat", json=no_summarize_request)
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            # Content type might include charset, so check if it starts with text/event-stream
            self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
    
    def test_chat_with_custom_title(self):
        """Test the POST /api/chat endpoint with a custom title."""
        # Update the chat request to include a custom title
        titled_request = self.chat_request.copy()
        titled_request["title"] = "Custom Conversation Title"
        
        # Mock the create_conversation, add_message, and get_message_history functions
        with patch("routes.chat.create_conversation", return_value=self.mock_conversation), \
             patch("routes.chat.add_message", return_value=MagicMock()), \
             patch("routes.chat.get_message_history", return_value=self.mock_messages):
            
            # Make the request
            response = self.client.post("/api/chat", json=titled_request)
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            # Content type might include charset, so check if it starts with text/event-stream
            self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))


if __name__ == "__main__":
    unittest.main()
