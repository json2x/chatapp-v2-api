"""
Tests for the models API endpoints.

This module tests the following endpoints:
- GET /api/models
- GET /api/models/{provider}
- GET /api/models-default
"""

import unittest
from unittest.mock import MagicMock, patch
from tests.test_base import BaseTest


class TestModelsEndpoints(BaseTest):
    """Test the models API endpoints."""
    
    def setUp(self):
        """Set up before each test."""
        super().setUp()
        self.mock_llm_service()
    
    def test_get_all_models(self):
        """Test the GET /api/models endpoint."""
        # Make the request
        response = self.client.get("/api/models")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "openai": ["gpt-4o-mini", "gpt-4o"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-sonnet-4-20250514"]
        })
    
    def test_get_provider_models_openai(self):
        """Test the GET /api/models/openai endpoint."""
        # Make the request
        response = self.client.get("/api/models/openai")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["gpt-4o-mini", "gpt-4o"])
    
    def test_get_provider_models_anthropic(self):
        """Test the GET /api/models/anthropic endpoint."""
        # Make the request
        response = self.client.get("/api/models/anthropic")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["claude-3-5-haiku-20241022", "claude-sonnet-4-20250514"])
    
    def test_get_provider_models_invalid_provider(self):
        """Test the GET /api/models/{provider} endpoint with an invalid provider."""
        # Make the request
        response = self.client.get("/api/models/invalid")
        
        # Check the response
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid provider", response.json()["detail"])
    
    def test_get_provider_models_unavailable_provider(self):
        """Test the GET /api/models/{provider} endpoint with an unavailable provider."""
        # Mock the LLM service to return no models for a provider
        with patch("llm_service_providers.index.llm_service.get_available_models", 
                  return_value={"openai": ["gpt-4o-mini", "gpt-4o"]}):
            # Make the request
            response = self.client.get("/api/models/anthropic")
            
            # Check the response
            self.assertEqual(response.status_code, 404)
            self.assertIn("not available", response.json()["detail"])
    
    def test_get_default_models(self):
        """Test the GET /api/models-default endpoint."""
        # Make the request
        response = self.client.get("/api/models-default")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022"
        })
    
    def test_get_default_models_partial_availability(self):
        """Test the GET /api/models-default endpoint with partial provider availability."""
        # Mock the LLM service to return models for only one provider
        with patch("llm_service_providers.index.llm_service.get_available_models", 
                  return_value={"openai": ["gpt-4o-mini", "gpt-4o"]}):
            # Make the request
            response = self.client.get("/api/models-default")
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "openai": "gpt-4o-mini"
            })


if __name__ == "__main__":
    unittest.main()
