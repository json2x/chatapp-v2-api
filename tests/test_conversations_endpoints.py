"""
Tests for the conversations API endpoints.

This module tests the following endpoints:
- GET /api/conversations
- GET /api/conversations/{conversation_id}
- DELETE /api/conversations/{conversation_id}
"""

import unittest
from unittest.mock import MagicMock, patch
from tests.test_base import BaseTest
from database.crud import get_all_conversations, get_conversation, delete_conversation


class TestConversationsEndpoints(BaseTest):
    """Test the conversations API endpoints."""
    
    def test_list_conversations(self):
        """Test the GET /api/conversations endpoint."""
        # Create mock conversations
        mock_conversations = [self.create_mock_conversation_dict(include_messages=False) for _ in range(5)]
        
        # Debug: Print mock data
        print("\nMock conversations:")
        for i, conv in enumerate(mock_conversations):
            print(f"Conv {i}: {conv.keys()}")
        
        # Mock the get_all_conversations function at the module level where it's used
        with patch("routes.conversations.get_all_conversations", return_value=mock_conversations):
            # Make the request
            response = self.client.get("/api/conversations?user_id=test-user&limit=10&offset=0")
            
            # Debug: Print response
            print(f"\nResponse status: {response.status_code}")
            print(f"Response JSON: {response.json()}")
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 5)
    
    def test_get_conversation_by_id(self):
        """Test the GET /api/conversations/{conversation_id} endpoint."""
        # Create a mock conversation
        mock_conversation = self.create_mock_conversation_dict(include_messages=True)
        
        # Mock the get_conversation function
        with patch("routes.conversations.get_conversation", return_value=mock_conversation):
            # Make the request
            response = self.client.get(f"/api/conversations/{mock_conversation['id']}")
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["id"], mock_conversation["id"])
            self.assertEqual(response.json()["title"], mock_conversation["title"])
            self.assertIn("messages", response.json())
            self.assertEqual(len(response.json()["messages"]), 3)
            
            # We're patching at the module level, so we can't verify the function calls directly
    
    def test_get_conversation_by_id_not_found(self):
        """Test the GET /api/conversations/{conversation_id} endpoint with a non-existent ID."""
        # Mock the get_conversation function to return None
        with patch("routes.conversations.get_conversation", return_value=None):
            # Make the request
            response = self.client.get("/api/conversations/non-existent-id")
            
            # Check the response
            self.assertEqual(response.status_code, 404)
            self.assertIn("not found", response.json()["detail"])
    
    def test_delete_conversation_by_id(self):
        """Test the DELETE /api/conversations/{conversation_id} endpoint."""
        # Create a mock conversation
        mock_conversation = self.create_mock_conversation_dict(include_messages=False)
        
        # Mock the get_conversation and delete_conversation functions
        with patch("routes.conversations.get_conversation", return_value=mock_conversation), \
             patch("routes.conversations.delete_conversation", return_value=True):
            # Make the request
            response = self.client.delete(f"/api/conversations/{mock_conversation['id']}")
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            self.assertIn("deleted successfully", response.json()["message"])
            
            # We're patching at the module level, so we can't verify the function calls directly
    
    def test_delete_conversation_by_id_not_found(self):
        """Test the DELETE /api/conversations/{conversation_id} endpoint with a non-existent ID."""
        # Mock the get_conversation function to return None
        with patch("routes.conversations.get_conversation", return_value=None):
            # Make the request
            response = self.client.delete("/api/conversations/non-existent-id")
            
            # Check the response
            self.assertEqual(response.status_code, 404)
            self.assertIn("not found", response.json()["detail"])
    
    def test_delete_conversation_by_id_failure(self):
        """Test the DELETE /api/conversations/{conversation_id} endpoint with a deletion failure."""
        # Create a mock conversation
        mock_conversation = self.create_mock_conversation_dict(include_messages=False)
        
        # Mock the get_conversation and delete_conversation functions
        with patch("routes.conversations.get_conversation", return_value=mock_conversation), \
             patch("routes.conversations.delete_conversation", return_value=False):
            # Make the request
            response = self.client.delete(f"/api/conversations/{mock_conversation['id']}")
            
            # Check the response
            self.assertEqual(response.status_code, 500)
            self.assertIn("Failed to delete", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
