#!/usr/bin/env python3
"""
Demonstration script for testing streaming functionality with visual output.
Run this script to see the streaming responses in real-time in your terminal.

Usage:
    python demo_streaming.py openai
    python demo_streaming.py anthropic
    python demo_streaming.py both
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Any, Generator
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_service_providers.openai import OpenAIChat
from llm_service_providers.anthropic import AnthropicChat


def display_openai_stream():
    """Demonstrate OpenAI streaming with visual output."""
    print("\n" + "="*80)
    print("OPENAI STREAMING DEMO")
    print("="*80)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return False
    
    try:
        openai_chat = OpenAIChat(api_key=api_key)
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 10 slowly, with a brief pause between each number."}
        ]
        
        print("\nPrompt: Count from 1 to 10 slowly")
        print("\nResponse:")
        
        # Stream the response and display it
        for chunk in openai_chat.stream_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        ):
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                # Add a small delay to simulate slower streaming for demo purposes
                time.sleep(0.01)
        
        print("\n\nStreaming complete!")
        return True
    
    except Exception as e:
        print(f"\nError during OpenAI streaming: {e}")
        return False


def display_anthropic_stream():
    """Demonstrate Anthropic streaming with visual output."""
    print("\n" + "="*80)
    print("ANTHROPIC STREAMING DEMO")
    print("="*80)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    try:
        anthropic_chat = AnthropicChat(api_key=api_key)
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 10 slowly, with a brief pause between each number."}
        ]
        
        print("\nPrompt: Count from 1 to 10 slowly")
        print("\nResponse:")
        
        # Stream the response and display it
        for event in anthropic_chat.stream_chat_completion(
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        ):
            if event.type == "content_block_delta":
                print(event.delta.text, end="", flush=True)
                # Add a small delay to simulate slower streaming for demo purposes
                time.sleep(0.01)
        
        print("\n\nStreaming complete!")
        return True
    
    except Exception as e:
        print(f"\nError during Anthropic streaming: {e}")
        return False


def display_side_by_side():
    """Run both streaming demos side by side using threads."""
    print("\n" + "="*80)
    print("SIDE-BY-SIDE STREAMING DEMO")
    print("="*80)
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return False
    
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    try:
        # Create the chat instances
        openai_chat = OpenAIChat(api_key=openai_key)
        anthropic_chat = AnthropicChat(api_key=anthropic_key)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a haiku about artificial intelligence."}
        ]
        
        print("\nPrompt: Write a haiku about artificial intelligence")
        print("\nResponses:")
        print("OpenAI: ", end="")
        
        # Get the full responses (we'll display them differently)
        openai_response = openai_chat.get_full_completion_from_stream(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print(openai_response)
        
        print("Anthropic: ", end="")
        
        anthropic_response = anthropic_chat.get_full_completion_from_stream(
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print(anthropic_response)
        
        print("\nComparison complete!")
        return True
    
    except Exception as e:
        print(f"\nError during side-by-side demo: {e}")
        return False


def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Demonstrate LLM streaming capabilities")
    parser.add_argument("provider", choices=["openai", "anthropic", "both", "compare"],
                        help="Which provider to demonstrate")
    
    args = parser.parse_args()
    
    if args.provider == "openai":
        display_openai_stream()
    elif args.provider == "anthropic":
        display_anthropic_stream()
    elif args.provider == "both":
        display_openai_stream()
        display_anthropic_stream()
    elif args.provider == "compare":
        display_side_by_side()


if __name__ == "__main__":
    main()
