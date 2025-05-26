import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import time
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app
from misc.db import get_db_connection


class TestPreviewColumns(unittest.TestCase):
    """Test cases for the conversation preview columns."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        
        # Create a mock for the LLM service
        self.llm_service_patcher = patch('routes.chat.llm_service')
        self.mock_llm_service = self.llm_service_patcher.start()
        
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
            assistant_response = "Hello, I'm an AI assistant."
            for text in assistant_response:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta = MagicMock()
                mock_chunk.choices[0].delta.content = text
                yield mock_chunk
        
        # Set the mock for stream_chat
        self.mock_llm_service.stream_chat.return_value = mock_stream()
        
        # Clean up any test conversation from previous runs
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE title LIKE 'Test Preview%'")
            conn.commit()
    
    def tearDown(self):
        """Clean up after tests."""
        self.llm_service_patcher.stop()
        
        # Clean up test data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE title LIKE 'Test Preview%'")
            conn.commit()
    
    def test_preview_columns_populated(self):
        """Test that the first_user_message and first_assistant_message columns are populated correctly."""
        # Make a request to the chat endpoint
        user_message = "Test Preview Message"
        response = self.client.post(
            "/api/chat",
            json={
                "model": "gpt-4o-mini",
                "message": user_message
            }
        )
        
        # Check that the response is a streaming response
        self.assertEqual(response.status_code, 200)
        
        # Parse the streamed response to get the conversation ID
        conversation_id = None
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    if data.get("done", False):
                        conversation_id = data.get("conversation_id")
                        break
        
        self.assertIsNotNone(conversation_id, "Conversation ID should be returned in the response")
        print(f"Created conversation with ID: {conversation_id}")
        
        # Add a small delay to ensure database operations complete
        time.sleep(1)
        
        # Query the database to check if the preview columns are populated
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First check if the conversation exists
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conversation = cursor.fetchone()
            self.assertIsNotNone(conversation, f"Conversation {conversation_id} should exist in the database")
            
            # Print all columns for debugging
            print("Conversation columns:")
            for key in conversation.keys():
                print(f"  {key}: {conversation[key]}")
            
            # Now check the specific columns we're interested in
            cursor.execute(
                "SELECT first_user_message, first_assistant_message FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = cursor.fetchone()
            
            self.assertIsNotNone(row, "Conversation should exist in the database")
            
            # Check first_user_message
            self.assertEqual(
                row['first_user_message'], 
                user_message, 
                f"first_user_message should be populated with the user message. Got: {row['first_user_message']}"
            )
            
            # Check first_assistant_message
            self.assertEqual(
                row['first_assistant_message'], 
                "Hello, I'm an AI assistant.", 
                f"first_assistant_message should be populated with the assistant's response. Got: {row['first_assistant_message']}"
            )
    
    def test_long_message_truncation(self):
        """Test that long messages are properly truncated in the preview columns."""
        # Create a long message (over 100 characters)
        long_message = "This is a very long message that should be truncated in the preview columns. " * 3
        
        # Make a request to the chat endpoint
        response = self.client.post(
            "/api/chat",
            json={
                "model": "gpt-4o-mini",
                "message": long_message
            }
        )
        
        # Check that the response is a streaming response
        self.assertEqual(response.status_code, 200)
        
        # Parse the streamed response to get the conversation ID
        conversation_id = None
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    if data.get("done", False):
                        conversation_id = data.get("conversation_id")
                        break
        
        self.assertIsNotNone(conversation_id, "Conversation ID should be returned in the response")
        print(f"Created conversation with ID: {conversation_id} for long message test")
        
        # Add a small delay to ensure database operations complete
        time.sleep(1)
        
        # Query the database to check if the preview columns are populated and truncated
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First check if the conversation exists
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conversation = cursor.fetchone()
            self.assertIsNotNone(conversation, f"Conversation {conversation_id} should exist in the database")
            
            # Print all columns for debugging
            print("Conversation columns for long message test:")
            for key in conversation.keys():
                print(f"  {key}: {conversation[key]}")
            
            # Now check the specific column we're interested in
            cursor.execute(
                "SELECT first_user_message FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = cursor.fetchone()
            
            self.assertIsNotNone(row, "Conversation should exist in the database")
            
            # Check if first_user_message exists and is not None
            self.assertIsNotNone(row['first_user_message'], "first_user_message should not be None")
            
            # Check first_user_message is truncated to 100 characters
            self.assertEqual(
                len(row['first_user_message']), 
                100, 
                f"first_user_message should be truncated to 100 characters. Got length: {len(row['first_user_message']) if row['first_user_message'] else 'None'}"
            )
            self.assertEqual(
                row['first_user_message'], 
                long_message[:100], 
                f"first_user_message should contain the first 100 characters of the message. Got: {row['first_user_message']}"
            )


if __name__ == '__main__':
    unittest.main()
