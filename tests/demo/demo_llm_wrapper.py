#!/usr/bin/env python3
"""
Demonstration script for testing the LLM service wrapper with streaming functionality.
This script tests both OpenAI and Anthropic default models using the unified interface.

Usage:
    python demo_llm_wrapper.py openai
    python demo_llm_wrapper.py anthropic
    python demo_llm_wrapper.py both
    python demo_llm_wrapper.py compare
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Any, Generator
import threading
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the LLM service wrapper
from llm_service_providers.index import llm_service
from misc.constants import Provider, DEFAULT_MODELS

# Load environment variables from .env file
load_dotenv()


def process_stream_chunk(chunk, provider_name):
    """Process a stream chunk based on the provider."""
    if provider_name == Provider.OPENAI:
        content = chunk.choices[0].delta.content
        if content:
            return content
    elif provider_name == Provider.ANTHROPIC:
        if chunk.type == "content_block_delta":
            return chunk.delta.text
    return ""


def display_provider_stream(provider_name):
    """Demonstrate streaming with a specific provider using its default model."""
    model = DEFAULT_MODELS[provider_name]
    provider_display_name = provider_name.upper()
    
    print("\n" + "="*80)
    print(f"{provider_display_name} STREAMING DEMO (Model: {model})")
    print("="*80)
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 10 slowly, with a brief pause between each number."}
        ]
        
        print("\nPrompt: Count from 1 to 10 slowly")
        print("\nResponse:")
        
        # Stream the response and display it
        for chunk in llm_service.stream_chat(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=100
        ):
            content = process_stream_chunk(chunk, provider_name)
            if content:
                print(content, end="", flush=True)
                # Add a small delay to simulate slower streaming for demo purposes
                time.sleep(0.01)
        
        print("\n\nStreaming complete!")
        return True
    
    except Exception as e:
        print(f"\nError during {provider_display_name} streaming: {e}")
        return False


def display_side_by_side():
    """Compare responses from both providers side by side."""
    openai_model = DEFAULT_MODELS[Provider.OPENAI]
    anthropic_model = DEFAULT_MODELS[Provider.ANTHROPIC]
    
    print("\n" + "="*80)
    print(f"SIDE-BY-SIDE COMPARISON")
    print(f"OpenAI: {openai_model} vs Anthropic: {anthropic_model}")
    print("="*80)
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a haiku about artificial intelligence."}
        ]
        
        print("\nPrompt: Write a haiku about artificial intelligence")
        print("\nResponses:")
        
        # Get OpenAI response
        print(f"OpenAI ({openai_model}): ", end="")
        openai_response = llm_service.get_chat_completion(
            model=openai_model,
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        print(openai_response)
        
        # Get Anthropic response
        print(f"\nAnthropic ({anthropic_model}): ", end="")
        anthropic_response = llm_service.get_chat_completion(
            model=anthropic_model,
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        print(anthropic_response)
        
        print("\nComparison complete!")
        return True
    
    except Exception as e:
        print(f"\nError during comparison: {e}")
        return False


def display_available_models():
    """Display all available models grouped by provider."""
    print("\n" + "="*80)
    print("AVAILABLE MODELS")
    print("="*80)
    
    available_models = llm_service.get_available_models()
    
    for provider, models in available_models.items():
        print(f"\n{provider.upper()} Models:")
        for model in models:
            if model == DEFAULT_MODELS.get(provider):
                print(f"  * {model} (DEFAULT)")
            else:
                print(f"  - {model}")
    
    print("\n")


def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Demonstrate LLM service wrapper with streaming")
    parser.add_argument("provider", choices=["openai", "anthropic", "both", "compare", "models"],
                        help="Which provider to demonstrate or action to perform")
    
    args = parser.parse_args()
    
    if args.provider == "openai":
        display_provider_stream(Provider.OPENAI)
    elif args.provider == "anthropic":
        display_provider_stream(Provider.ANTHROPIC)
    elif args.provider == "both":
        display_provider_stream(Provider.OPENAI)
        display_provider_stream(Provider.ANTHROPIC)
    elif args.provider == "compare":
        display_side_by_side()
    elif args.provider == "models":
        display_available_models()


if __name__ == "__main__":
    main()
