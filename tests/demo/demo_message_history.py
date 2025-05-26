#!/usr/bin/env python3
"""
Demo script for testing the message history functionality.

This script demonstrates the get_message_history function with various scenarios:
1. Creating a conversation with a large number of messages
2. Retrieving the conversation history with summarization
3. Retrieving the conversation history without summarization
4. Comparing the two approaches
"""

import os
import sys
import uuid
import json
import argparse
import time
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_service_providers.index import llm_service
from misc.db import create_conversation, add_message, get_conversation, delete_conversation
from misc.constants import CONVERSATION_MESSAGES_THRESHOLD


def create_demo_conversation(num_messages: int = 30) -> str:
    """
    Create a demo conversation with the specified number of messages.
    
    Args:
        num_messages: Number of messages to create (default: 30)
        
    Returns:
        The ID of the created conversation
    """
    # Create a new conversation
    conversation_id = create_conversation(
        title=f"Demo Conversation ({num_messages} messages)",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant."
    )
    
    # Add messages to the conversation
    for i in range(num_messages):
        role = 'user' if i % 2 == 0 else 'assistant'
        
        if role == 'user':
            if i == 0:
                content = "Hello, I'd like to learn about artificial intelligence."
            elif i < 10:
                topics = ["machine learning", "neural networks", "deep learning", 
                          "natural language processing", "computer vision"]
                content = f"Can you tell me more about {topics[i//2 % len(topics)]}?"
            elif i < 20:
                content = f"That's interesting. How is this used in real-world applications? (Message {i})"
            else:
                content = f"I see. What about ethical considerations? (Message {i})"
        else:
            if i == 1:
                content = "Hello! I'd be happy to help you learn about artificial intelligence."
            elif i < 11:
                content = f"Certainly! {['Machine learning', 'Neural networks', 'Deep learning', 'NLP', 'Computer vision'][i//2 % 5]} is a fascinating field. It involves... (Message {i})"
            elif i < 21:
                content = f"There are many applications in industries like healthcare, finance, and transportation. For example... (Message {i})"
            else:
                content = f"Ethical considerations are very important. We need to consider issues like bias, privacy, and transparency... (Message {i})"
        
        add_message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
    
    print(f"Created conversation with ID: {conversation_id}")
    print(f"Added {num_messages} messages to the conversation")
    
    return conversation_id


def display_messages(messages: List[Dict[str, str]], title: str = "Messages"):
    """Display a list of messages in a readable format."""
    print(f"\n{title} ({len(messages)} messages):")
    print("-" * 80)
    
    for i, msg in enumerate(messages):
        role = msg['role'].upper()
        content = msg['content']
        
        # Truncate long messages for display
        if len(content) > 100:
            content = content[:97] + "..."
        
        print(f"{i+1}. [{role}]: {content}")
    
    print("-" * 80)


def demo_message_history(conversation_id: str):
    """
    Demonstrate the get_message_history function with and without summarization.
    
    Args:
        conversation_id: ID of the conversation to use
    """
    print("\n=== Message History Demo ===")
    
    # Get the conversation from the database
    conversation = get_conversation(conversation_id)
    if not conversation:
        print(f"Conversation with ID {conversation_id} not found")
        return
    
    print(f"Conversation: {conversation['title']}")
    print(f"Total messages: {len(conversation['messages'])}")
    print(f"Threshold for summarization: {CONVERSATION_MESSAGES_THRESHOLD}")
    
    # Get message history with summarization (default)
    start_time = time.time()
    summarized_messages = llm_service.get_message_history(conversation_id)
    summarize_time = time.time() - start_time
    
    # Get message history without summarization
    start_time = time.time()
    full_messages = llm_service.get_message_history(conversation_id, summarize=False)
    no_summarize_time = time.time() - start_time
    
    # Display the results
    display_messages(summarized_messages, "Messages with Summarization")
    print(f"Time taken: {summarize_time:.4f} seconds")
    
    display_messages(full_messages, "Messages without Summarization")
    print(f"Time taken: {no_summarize_time:.4f} seconds")
    
    # Display comparison
    print("\nComparison:")
    print(f"- With summarization: {len(summarized_messages)} messages ({summarize_time:.4f}s)")
    print(f"- Without summarization: {len(full_messages)} messages ({no_summarize_time:.4f}s)")
    
    # Check if summarization was applied
    if len(summarized_messages) != len(full_messages):
        print("\nSummarization was applied!")
        if summarized_messages[0]['role'] == 'system' and 'Summary of previous conversation' in summarized_messages[0]['content']:
            print("First message contains the summary of older messages:")
            print("-" * 80)
            print(summarized_messages[0]['content'])
            print("-" * 80)


def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description='Demo for message history functionality')
    parser.add_argument('--create', action='store_true', help='Create a new demo conversation')
    parser.add_argument('--conversation-id', type=str, help='Use an existing conversation ID')
    parser.add_argument('--messages', type=int, default=30, help='Number of messages to create (default: 30)')
    parser.add_argument('--delete', action='store_true', help='Delete the conversation after the demo')
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment.")
        return
    
    conversation_id = None
    
    # Create a new conversation or use an existing one
    if args.create:
        conversation_id = create_demo_conversation(args.messages)
    elif args.conversation_id:
        conversation_id = args.conversation_id
    else:
        # If neither option is provided, create a new conversation
        print("No conversation ID provided. Creating a new demo conversation...")
        conversation_id = create_demo_conversation(args.messages)
    
    # Run the demo
    demo_message_history(conversation_id)
    
    # Delete the conversation if requested
    if args.delete and conversation_id:
        delete_conversation(conversation_id)
        print(f"\nDeleted conversation with ID: {conversation_id}")


if __name__ == '__main__':
    main()
