"""
Constants for the chatapp-v2-api application.
"""

# LLM Provider enum
class Provider:
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Model to provider mapping
MODEL_PROVIDER_MAP = {
    # OpenAI models
    "gpt-4o-mini": Provider.OPENAI,
    "gpt-4o": Provider.OPENAI,
    "gpt-4.1": Provider.OPENAI,
    "gpt-4.1-mini": Provider.OPENAI,
    "gpt-3.5-turbo": Provider.OPENAI,
    
    # Anthropic models
    "claude-3-5-haiku-20241022": Provider.ANTHROPIC,
    "claude-3-opus-20240229": Provider.ANTHROPIC,
    "claude-3-sonnet-20240229": Provider.ANTHROPIC,
    "claude-3-haiku-20240307": Provider.ANTHROPIC,
}


# Default models for each provider
DEFAULT_MODELS = {
    Provider.OPENAI: "gpt-4o-mini",
    Provider.ANTHROPIC: "claude-3-5-haiku-20241022",
}


# Conversation settings
CONVERSATION_MESSAGES_THRESHOLD = 20  # Maximum number of messages to include before summarizing

# Model capabilities and features
MODEL_CAPABILITIES = {
    # OpenAI models
    "gpt-4o-mini": {
        "max_tokens": 8192,
        "supports_vision": True,
        "description": "Smaller, faster version of GPT-4o"
    },
    "gpt-4o": {
        "max_tokens": 8192,
        "supports_vision": True,
        "description": "Most capable OpenAI model with vision capabilities"
    },
    "gpt-4.1": {
        "max_tokens": 8192,
        "supports_vision": True,
        "description": "Latest GPT-4 model with improved reasoning"
    },
    "gpt-4.1-mini": {
        "max_tokens": 8192,
        "supports_vision": True,
        "description": "Smaller, faster version of GPT-4.1"
    },
    
    # Anthropic models
    "claude-sonnet-4-20250514": {
        "max_tokens": 200000,
        "supports_vision": True,
        "description": "Smart, efficient model for every day use"
    },
    "claude-3-5-haiku-20241022": {
        "max_tokens": 200000,
        "supports_vision": True,
        "description": "Latest Claude model, fast and efficient"
    },
    "claude-3-sonnet-20240229": {
        "max_tokens": 200000,
        "supports_vision": True,
        "description": "Balanced Claude model for performance and capability"
    },
    "claude-3-haiku-20240307": {
        "max_tokens": 200000,
        "supports_vision": True,
        "description": "Fastest Claude model"
    },
}