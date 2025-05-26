import os
import sys
import unittest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app


class TestConversationsEndpoints(unittest.TestCase):
    """Test cases for the conversations endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        
        # Create mocks for the database functions
        self.get_all_conversations_patcher = patch('routes.conversations.get_all_conversations')
        self.mock_get_all_conversations = self.get_all_conversations_patcher.start()
        
        self.get_conversation_patcher = patch('routes.conversations.get_conversation')
        self.mock_get_conversation = self.get_conversation_patcher.start()
        
        self.delete_conversation_patcher = patch('routes.conversations.delete_conversation')
        self.mock_delete_conversation = self.delete_conversation_patcher.start()
        
        # Set up default return values
        self.conversation_id = str(uuid.uuid4())
        self.mock_conversation = {
            'id': self.conversation_id,
            'title': 'Test Conversation',
            'created_at': '2025-05-25T13:00:00',
            'updated_at': '2025-05-25T13:10:00',
            'model': 'gpt-4o-mini',
            'messages': [
                {
                    'id': str(uuid.uuid4()),
                    'conversation_id': self.conversation_id,
                    'role': 'user',
                    'content': 'Hello',
                    'created_at': '2025-05-25T13:00:00'
                },
                {
                    'id': str(uuid.uuid4()),
                    'conversation_id': self.conversation_id,
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'created_at': '2025-05-25T13:00:10'
                }
            ]
        }
        
        self.mock_conversations_list = [
            {
                'id': self.conversation_id,
                'title': 'Test Conversation',
                'created_at': '2025-05-25T13:00:00',
                'updated_at': '2025-05-25T13:10:00',
                'user_id': None,
                'model': 'gpt-4o-mini',
                'system_prompt': None,
                'first_user_message': 'Hello',
                'first_assistant_message': 'Hi there!',
                'message_count': 2,
                'metadata': None
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Another Conversation',
                'created_at': '2025-05-25T14:00:00',
                'updated_at': '2025-05-25T14:10:00',
                'user_id': None,
                'model': 'claude-3-5-haiku-20241022',
                'system_prompt': None,
                'first_user_message': 'What is AI?',
                'first_assistant_message': 'AI stands for Artificial Intelligence...',
                'message_count': 2,
                'metadata': None
            }
        ]
        
        self.mock_get_all_conversations.return_value = self.mock_conversations_list
        self.mock_get_conversation.return_value = self.mock_conversation
    
    def tearDown(self):
        """Clean up after tests."""
        self.get_all_conversations_patcher.stop()
        self.get_conversation_patcher.stop()
        self.delete_conversation_patcher.stop()
    
    def test_list_conversations(self):
        """Test the GET /api/conversations endpoint."""
        # Make a request to the conversations endpoint
        response = self.client.get("/api/conversations")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['id'], self.conversation_id)
        self.assertEqual(data[0]['title'], 'Test Conversation')
        
        # Verify that get_all_conversations was called with the default parameters
        self.mock_get_all_conversations.assert_called_once_with(user_id=None, limit=100, offset=0)
    
    def test_list_conversations_with_user_id(self):
        """Test the GET /api/conversations endpoint with user_id filter."""
        # Make a request with a user_id filter
        user_id = "test_user"
        response = self.client.get(f"/api/conversations?user_id={user_id}")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify that get_all_conversations was called with the user_id parameter
        self.mock_get_all_conversations.assert_called_once_with(user_id=user_id, limit=100, offset=0)
    
    def test_list_conversations_with_pagination(self):
        """Test the GET /api/conversations endpoint with pagination."""
        # Make a request with pagination parameters
        limit = 10
        offset = 5
        response = self.client.get(f"/api/conversations?limit={limit}&offset={offset}")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify that get_all_conversations was called with the pagination parameters
        self.mock_get_all_conversations.assert_called_once_with(user_id=None, limit=limit, offset=offset)
    
    def test_get_conversation_by_id(self):
        """Test the GET /api/conversations/{conversation_id} endpoint."""
        # Make a request to get a specific conversation
        response = self.client.get(f"/api/conversations/{self.conversation_id}")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertEqual(data['id'], self.conversation_id)
        self.assertEqual(data['title'], 'Test Conversation')
        self.assertEqual(len(data['messages']), 2)
        
        # Verify that get_conversation was called with the conversation_id
        self.mock_get_conversation.assert_called_once_with(self.conversation_id)
    
    def test_get_conversation_by_id_not_found(self):
        """Test the GET /api/conversations/{conversation_id} endpoint with a non-existent ID."""
        # Set up the mock to return None (conversation not found)
        self.mock_get_conversation.return_value = None
        
        # Make a request with a non-existent ID
        non_existent_id = str(uuid.uuid4())
        response = self.client.get(f"/api/conversations/{non_existent_id}")
        
        # Check that we get a 404 error
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Conversation not found')
        
        # Verify that get_conversation was called with the non-existent ID
        self.mock_get_conversation.assert_called_once_with(non_existent_id)
    
    def test_delete_conversation(self):
        """Test the DELETE /api/conversations/{conversation_id} endpoint."""
        # Make a request to delete a conversation
        response = self.client.delete(f"/api/conversations/{self.conversation_id}")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertIn('deleted successfully', response.json()['message'])
        
        # Verify that get_conversation was called to check if the conversation exists
        self.mock_get_conversation.assert_called_once_with(self.conversation_id)
        
        # Verify that delete_conversation was called with the conversation_id
        self.mock_delete_conversation.assert_called_once_with(self.conversation_id)
    
    def test_delete_conversation_not_found(self):
        """Test the DELETE /api/conversations/{conversation_id} endpoint with a non-existent ID."""
        # Set up the mock to return None (conversation not found)
        self.mock_get_conversation.return_value = None
        
        # Make a request with a non-existent ID
        non_existent_id = str(uuid.uuid4())
        response = self.client.delete(f"/api/conversations/{non_existent_id}")
        
        # Check that we get a 404 error
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Conversation not found')
        
        # Verify that get_conversation was called with the non-existent ID
        self.mock_get_conversation.assert_called_once_with(non_existent_id)
        
        # Verify that delete_conversation was NOT called
        self.mock_delete_conversation.assert_not_called()


if __name__ == '__main__':
    unittest.main()
