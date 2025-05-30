"""
Base test utilities for the chatapp-v2-api tests.

This module provides common functionality used across all test files.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import uuid
import json
from typing import Dict, List, Any, Optional

# Import the FastAPI app
from main import app
from database.database import get_db, set_test_mode
from database.models import ConversationModel, MessageModel
from llm_service_providers.index import llm_service


class BaseTest(unittest.TestCase):
    """Base test class with common setup and utility methods."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Enable test mode for the database
        set_test_mode(True)
        
        # Create a test client
        cls.client = TestClient(app)
        
        # Create a mock session
        cls.mock_db = MagicMock()
        
        # Set up the dependency override
        app.dependency_overrides[get_db] = lambda: cls.mock_db
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Disable test mode
        set_test_mode(False)
        
        # Remove the dependency override
        app.dependency_overrides.clear()
    
    def setUp(self):
        """Set up before each test."""
        # Reset the mock
        self.mock_db.reset_mock()
    
    def create_mock_conversation_dict(self, include_messages: bool = True) -> Dict[str, Any]:
        """Create a mock conversation dictionary."""
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create a conversation dictionary
        conversation = {
            "id": conv_id,
            "title": "Test Conversation",
            "created_at": now,
            "updated_at": now,
            "user_id": "test-user",
            "model": "gpt-4o-mini",
            "system_prompt": "You are a helpful assistant.",
            "first_user_message": "Hello, how are you?",
            "first_assistant_message": "I'm doing well, thank you for asking!",
            "metadata": {"test": "metadata"},
            "message_count": 0
        }
        
        # Add messages if requested
        if include_messages:
            messages = []
            for i in range(3):
                msg = {
                    "id": str(uuid.uuid4()),
                    "conversation_id": conv_id,
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message {i+1}",
                    "created_at": now,
                    "tokens": 10,
                    "model": "gpt-4o-mini",
                    "metadata": {}
                }
                messages.append(msg)
            
            conversation["messages"] = messages
            conversation["message_count"] = len(messages)
        else:
            conversation["messages"] = []
        
        return conversation
    
    def create_mock_conversation(self, include_messages: bool = True):
        """Create a mock conversation object."""
        # Simply return the dictionary directly
        return self.create_mock_conversation_dict(include_messages=include_messages)
        
    def create_mock_conversations_list(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create a list of mock conversation objects."""
        return [self.create_mock_conversation(include_messages=False) for _ in range(count)]
    
    def mock_llm_service(self):
        """Mock the LLM service for testing."""
        # Mock the get_available_models method
        llm_service.get_available_models = MagicMock(return_value={
            "openai": ["gpt-4o-mini", "gpt-4o"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-sonnet-4-20250514"]
        })
        
        # Mock the stream_chat method
        llm_service.stream_chat = MagicMock(return_value=[
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))])
        ])
