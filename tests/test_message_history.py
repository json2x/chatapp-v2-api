import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import uuid
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service_providers.index import LLMServiceProvider
from misc.constants import Provider, CONVERSATION_MESSAGES_THRESHOLD


class TestMessageHistory(unittest.TestCase):
    """Test cases for message history functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock provider for testing
        self.mock_openai = MagicMock()
        
        # Create the service provider with mock providers
        self.llm_service = LLMServiceProvider()
        self.llm_service.providers = {
            Provider.OPENAI: self.mock_openai
        }
        
        # Mock the brief_summary_of_conversation_history method
        self.llm_service.brief_summary_of_conversation_history = MagicMock(
            return_value="- User asked about machine learning\n- Assistant explained the concept"
        )
    
    @patch('llm_service_providers.index.get_conversation')
    def test_get_message_history_not_found(self, mock_get_conversation):
        """Test handling of non-existent conversations."""
        # Set up the mock to return None (conversation not found)
        mock_get_conversation.return_value = None
        
        # Verify that a ValueError is raised
        with self.assertRaises(ValueError):
            self.llm_service.get_message_history(str(uuid.uuid4()))
    
    @patch('llm_service_providers.index.get_conversation')
    def test_get_message_history_short_conversation(self, mock_get_conversation):
        """Test handling of conversations that don't exceed the threshold."""
        # Create a mock conversation with a few messages
        conversation_id = str(uuid.uuid4())
        mock_messages = [
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'user', 'content': 'Hello', 'created_at': '2025-05-25T13:00:00'},
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'assistant', 'content': 'Hi there!', 'created_at': '2025-05-25T13:00:10'}
        ]
        mock_conversation = {
            'id': conversation_id,
            'title': 'Test Conversation',
            'messages': mock_messages
        }
        
        # Set up the mock to return our conversation
        mock_get_conversation.return_value = mock_conversation
        
        # Call the function
        result = self.llm_service.get_message_history(conversation_id)
        
        # Verify the result contains all messages in the expected format
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['role'], 'user')
        self.assertEqual(result[0]['content'], 'Hello')
        self.assertEqual(result[1]['role'], 'assistant')
        self.assertEqual(result[1]['content'], 'Hi there!')
        
        # Verify that summarization was not called
        self.llm_service.brief_summary_of_conversation_history.assert_not_called()
    
    @patch('llm_service_providers.index.get_conversation')
    def test_get_message_history_long_conversation_with_summarize(self, mock_get_conversation):
        """Test handling of conversations that exceed the threshold with summarization enabled."""
        # Create a mock conversation with more messages than the threshold
        conversation_id = str(uuid.uuid4())
        mock_messages = []
        
        # Create messages (CONVERSATION_MESSAGES_THRESHOLD + 10 messages)
        for i in range(CONVERSATION_MESSAGES_THRESHOLD + 10):
            role = 'user' if i % 2 == 0 else 'assistant'
            mock_messages.append({
                'id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'role': role,
                'content': f'Message {i}',
                'created_at': f'2025-05-25T13:{i:02d}:00'
            })
        
        mock_conversation = {
            'id': conversation_id,
            'title': 'Long Test Conversation',
            'messages': mock_messages
        }
        
        # Set up the mock to return our conversation
        mock_get_conversation.return_value = mock_conversation
        
        # Call the function with summarize=True (default)
        result = self.llm_service.get_message_history(conversation_id)
        
        # Verify the result contains the summary message + recent messages
        self.assertEqual(len(result), CONVERSATION_MESSAGES_THRESHOLD + 1)
        
        # Check that the first message is a system message with the summary
        self.assertEqual(result[0]['role'], 'system')
        self.assertTrue('Summary of previous conversation:' in result[0]['content'])
        
        # Check that the remaining messages are the most recent ones
        for i in range(1, CONVERSATION_MESSAGES_THRESHOLD + 1):
            # The index in the original messages list (starting from the end)
            original_idx = len(mock_messages) - CONVERSATION_MESSAGES_THRESHOLD + i - 1
            # Get the expected role directly from the mock messages
            expected_role = mock_messages[original_idx]['role']
            expected_content = mock_messages[original_idx]['content']
            
            self.assertEqual(result[i]['role'], expected_role)
            self.assertEqual(result[i]['content'], expected_content)
        
        # Verify that summarization was called with the older messages
        older_messages = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in mock_messages[:10]
        ]
        self.llm_service.brief_summary_of_conversation_history.assert_called_once()
    
    @patch('llm_service_providers.index.get_conversation')
    def test_get_message_history_long_conversation_without_summarize(self, mock_get_conversation):
        """Test handling of conversations that exceed the threshold with summarization disabled."""
        # Create a mock conversation with more messages than the threshold
        conversation_id = str(uuid.uuid4())
        mock_messages = []
        
        # Create messages (CONVERSATION_MESSAGES_THRESHOLD + 10 messages)
        for i in range(CONVERSATION_MESSAGES_THRESHOLD + 10):
            role = 'user' if i % 2 == 0 else 'assistant'
            mock_messages.append({
                'id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'role': role,
                'content': f'Message {i}',
                'created_at': f'2025-05-25T13:{i:02d}:00'
            })
        
        mock_conversation = {
            'id': conversation_id,
            'title': 'Long Test Conversation',
            'messages': mock_messages
        }
        
        # Set up the mock to return our conversation
        mock_get_conversation.return_value = mock_conversation
        
        # Call the function with summarize=False
        result = self.llm_service.get_message_history(conversation_id, summarize=False)
        
        # Verify the result contains all messages
        self.assertEqual(len(result), CONVERSATION_MESSAGES_THRESHOLD + 10)
        
        # Check that all messages are present in the correct order
        for i in range(CONVERSATION_MESSAGES_THRESHOLD + 10):
            expected_role = 'user' if i % 2 == 0 else 'assistant'
            expected_content = f'Message {i}'
            
            self.assertEqual(result[i]['role'], expected_role)
            self.assertEqual(result[i]['content'], expected_content)
        
        # Verify that summarization was not called
        self.llm_service.brief_summary_of_conversation_history.assert_not_called()
    
    @patch('llm_service_providers.index.get_conversation')
    def test_get_message_history_filters_invalid_roles(self, mock_get_conversation):
        """Test that messages with invalid roles are filtered out."""
        # Create a mock conversation with some invalid roles
        conversation_id = str(uuid.uuid4())
        mock_messages = [
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'user', 'content': 'Hello', 'created_at': '2025-05-25T13:00:00'},
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'invalid_role', 'content': 'This should be filtered', 'created_at': '2025-05-25T13:00:05'},
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'assistant', 'content': 'Hi there!', 'created_at': '2025-05-25T13:00:10'},
            {'id': str(uuid.uuid4()), 'conversation_id': conversation_id, 'role': 'another_invalid', 'content': 'Also filtered', 'created_at': '2025-05-25T13:00:15'}
        ]
        mock_conversation = {
            'id': conversation_id,
            'title': 'Test Conversation',
            'messages': mock_messages
        }
        
        # Set up the mock to return our conversation
        mock_get_conversation.return_value = mock_conversation
        
        # Call the function
        result = self.llm_service.get_message_history(conversation_id)
        
        # Verify the result only contains messages with valid roles
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['role'], 'user')
        self.assertEqual(result[0]['content'], 'Hello')
        self.assertEqual(result[1]['role'], 'assistant')
        self.assertEqual(result[1]['content'], 'Hi there!')


if __name__ == '__main__':
    unittest.main()
