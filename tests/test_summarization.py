import os
import unittest
from unittest.mock import patch, MagicMock
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service_providers.index import LLMServiceProvider
from misc.constants import Provider


class TestConversationSummarization(unittest.TestCase):
    """Test cases for conversation summarization functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock provider for testing
        self.mock_openai = MagicMock()
        self.mock_anthropic = MagicMock()
        
        # Create the service provider with mock providers
        self.llm_service = LLMServiceProvider()
        self.llm_service.providers = {
            Provider.OPENAI: self.mock_openai,
            Provider.ANTHROPIC: self.mock_anthropic
        }
    
    def test_resource_replacement(self):
        """Test that image and attachment references are replaced with <resource /> tags."""
        # Sample conversation with various types of media references
        test_messages = [
            {"role": "user", "content": "Here's an image: ![test image](https://example.com/image.jpg)"},
            {"role": "assistant", "content": "I see the image. Here's another one: <img src='https://example.com/image2.jpg' alt='test'>"},
            {"role": "user", "content": "And a base64 image: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."},
            {"role": "assistant", "content": "And an attachment: [attachment:file.pdf]"}
        ]
        
        # Mock the get_chat_completion method to return a predefined summary
        self.llm_service.get_chat_completion = MagicMock(return_value="- Test summary")
        
        # Call the function
        self.llm_service.brief_summary_of_conversation_history(test_messages)
        
        # Get the messages that were passed to get_chat_completion
        call_args = self.llm_service.get_chat_completion.call_args[1]
        messages = call_args['messages']
        
        # Extract the user message content which contains the processed conversation
        user_message_content = messages[1]['content']
        
        # Check that all media references were replaced with <resource /> tags
        self.assertIn("user: Here's an image: <resource />", user_message_content)
        self.assertIn("assistant: I see the image. Here's another one: <resource />", user_message_content)
        self.assertIn("user: And a base64 image: <resource />", user_message_content)
        self.assertIn("assistant: And an attachment: <resource />", user_message_content)
        
        # Verify no original media references remain
        self.assertNotIn("![test image]", user_message_content)
        self.assertNotIn("<img src", user_message_content)
        self.assertNotIn("data:image/jpeg;base64", user_message_content)
        self.assertNotIn("[attachment:", user_message_content)
    

    
    def test_summary_parameters(self):
        """Test that custom parameters are passed correctly."""
        # Sample conversation
        test_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        # Mock the get_chat_completion method
        self.llm_service.get_chat_completion = MagicMock(return_value="- Test summary")
        
        # Call with custom parameters
        self.llm_service.brief_summary_of_conversation_history(
            test_messages,
            max_tokens=300,
            temperature=0.7
        )
        
        # Verify the parameters were passed correctly
        self.llm_service.get_chat_completion.assert_called_with(
            model="gpt-4o-mini",
            messages=unittest.mock.ANY,
            max_tokens=300,
            temperature=0.7
        )
    
    @patch('llm_service_providers.index.LLMServiceProvider.get_chat_completion')
    def test_summary_format(self, mock_get_chat_completion):
        """Test that the summary is formatted correctly with bullet points."""
        # Sample conversation
        test_messages = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of AI that enables systems to learn from data."}
        ]
        
        # Set up the mock to return a bullet-point summary
        mock_summary = "- User asked about machine learning\n- Assistant explained that machine learning is a subset of AI\n- Assistant mentioned that ML systems learn from data"
        mock_get_chat_completion.return_value = mock_summary
        
        # Call the function
        summary = self.llm_service.brief_summary_of_conversation_history(test_messages)
        
        # Verify the summary format
        self.assertEqual(summary, mock_summary)
        self.assertTrue(summary.startswith("- "))
        self.assertTrue(all(line.startswith("- ") for line in summary.split("\n")))


if __name__ == '__main__':
    unittest.main()
