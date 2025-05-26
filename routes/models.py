from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from llm_service_providers.index import llm_service
from misc.constants import Provider

router = APIRouter()

@router.get("/models")
async def get_available_models():
    """
    Get all available models for chat completion.
    
    Returns a dictionary with providers as keys and lists of model names as values.
    Only includes models that are available for use with the current API keys.
    """
    return llm_service.get_available_models()


@router.get("/models/{provider}")
async def get_provider_models(provider: str):
    """
    Get available models for a specific provider.
    
    Args:
        provider: The provider name (e.g., "openai", "anthropic")
        
    Returns:
        A list of available model names for the specified provider
        
    Raises:
        HTTPException: If the provider is not valid or not available
    """
    # Check if the provider is valid
    if provider.lower() not in ["openai", "anthropic"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid provider: {provider}. Valid providers are: openai, anthropic"
        )
        
    # Get the provider enum value
    if provider.lower() == "openai":
        provider_enum = Provider.OPENAI
    else:  # anthropic
        provider_enum = Provider.ANTHROPIC
    
    # Get all available models
    available_models = llm_service.get_available_models()
    
    # Check if the provider is available
    if provider.lower() not in available_models:
        raise HTTPException(
            status_code=404,
            detail=f"Provider {provider} is not available. Check your API keys."
        )
    
    # Return the models for the specified provider
    return available_models[provider.lower()]


@router.get("/models-default")
async def get_default_models():
    """
    Get the default model for each available provider.
    
    Returns a dictionary with providers as keys and their default model names as values.
    Only includes providers that are available with the current API keys.
    """
    available_models = llm_service.get_available_models()
    default_models = {}
    
    for provider_name in available_models:
        # Get the default model for this provider
        if provider_name == "openai" and available_models[provider_name]:
            default_models[provider_name] = "gpt-4o-mini"
        elif provider_name == "anthropic" and available_models[provider_name]:
            default_models[provider_name] = "claude-3-5-haiku-20241022"
    
    return default_models
