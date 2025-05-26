import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app
from misc.constants import Provider


class TestModelsEndpoints(unittest.TestCase):
    """Test cases for the models endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        
        # Create a mock for the LLM service
        self.llm_service_patcher = patch('routes.models.llm_service')
        self.mock_llm_service = self.llm_service_patcher.start()
        
        # Set up default return values for get_available_models
        self.mock_llm_service.get_available_models.return_value = {
            "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-sonnet-4-20250514"]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        self.llm_service_patcher.stop()
    
    def test_get_all_models(self):
        """Test the GET /api/models endpoint."""
        # Make a request to the models endpoint
        response = self.client.get("/api/models")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("openai", data)
        self.assertIn("anthropic", data)
        self.assertIn("gpt-4o-mini", data["openai"])
        self.assertIn("claude-3-5-haiku-20241022", data["anthropic"])
        
        # Verify that get_available_models was called
        self.mock_llm_service.get_available_models.assert_called_once()
    
    def test_get_provider_models_openai(self):
        """Test the GET /api/models/{provider} endpoint for OpenAI."""
        # Make a request to the provider-specific endpoint
        response = self.client.get("/api/models/openai")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertIn("gpt-4o-mini", data)
        self.assertIn("gpt-4o", data)
        
        # Verify that get_available_models was called
        self.mock_llm_service.get_available_models.assert_called_once()
    
    def test_get_provider_models_anthropic(self):
        """Test the GET /api/models/{provider} endpoint for Anthropic."""
        # Make a request to the provider-specific endpoint
        response = self.client.get("/api/models/anthropic")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertIn("claude-3-5-haiku-20241022", data)
        
        # Verify that get_available_models was called
        self.mock_llm_service.get_available_models.assert_called_once()
    
    def test_get_provider_models_invalid_provider(self):
        """Test the GET /api/models/{provider} endpoint with an invalid provider."""
        # Make a request with an invalid provider
        response = self.client.get("/api/models/invalid_provider")
        
        # Check that we get a 400 error
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid provider", response.json()["detail"])
    
    def test_get_provider_models_unavailable_provider(self):
        """Test the GET /api/models/{provider} endpoint with a valid but unavailable provider."""
        # Set up the mock to return a response without the requested provider
        self.mock_llm_service.get_available_models.return_value = {
            "openai": ["gpt-4o-mini", "gpt-4o"]
        }
        
        # Make a request with a valid but unavailable provider
        response = self.client.get("/api/models/anthropic")
        
        # Check that we get a 404 error
        self.assertEqual(response.status_code, 404)
        self.assertIn("not available", response.json()["detail"])
    
    def test_get_default_models(self):
        """Test the GET /api/models-default endpoint."""
        # Make a request to the default models endpoint
        response = self.client.get("/api/models-default")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("openai", data)
        self.assertIn("anthropic", data)
        self.assertEqual(data["openai"], "gpt-4o-mini")
        self.assertEqual(data["anthropic"], "claude-3-5-haiku-20241022")
        
        # Verify that get_available_models was called
        self.mock_llm_service.get_available_models.assert_called_once()
    
    def test_get_default_models_partial_availability(self):
        """Test the GET /api/models-default endpoint with partial provider availability."""
        # Set up the mock to return a response with only one provider
        self.mock_llm_service.get_available_models.return_value = {
            "openai": ["gpt-4o-mini", "gpt-4o"]
        }
        
        # Make a request to the default models endpoint
        response = self.client.get("/api/models-default")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains only the available provider
        data = response.json()
        self.assertIn("openai", data)
        self.assertNotIn("anthropic", data)
        self.assertEqual(data["openai"], "gpt-4o-mini")


if __name__ == '__main__':
    unittest.main()
