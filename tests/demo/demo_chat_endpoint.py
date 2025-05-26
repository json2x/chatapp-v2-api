#!/usr/bin/env python3
"""
Demo script for testing the chat endpoint.

This script allows you to interactively test the chat endpoint by:
1. Prompting for a message to send to the model
2. Making a request to the chat endpoint
3. Displaying the streaming response in real-time
4. Optionally continuing the conversation with the same session

Usage:
    python demo_chat_endpoint.py [--host HOST] [--port PORT]
"""

import os
import sys
import json
import uuid
import argparse
import requests
import time
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def print_colored(text: str, color: str = "reset") -> None:
    """Print text with ANSI color codes."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
        "bold": "\033[1m"
    }
    
    start_color = colors.get(color.lower(), colors["reset"])
    end_color = colors["reset"]
    
    print(f"{start_color}{text}{end_color}")


def stream_chat(
    host: str,
    port: int,
    message: str,
    model: str = "gpt-4o-mini",
    conversation_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    summarize_history: bool = True
) -> Optional[str]:
    """
    Send a request to the chat endpoint and display the streaming response.
    
    Args:
        host: The hostname of the API server
        port: The port of the API server
        message: The message to send to the model
        model: The model to use (default: gpt-4o-mini)
        conversation_id: Optional ID of an existing conversation
        system_prompt: Optional system prompt to use
        summarize_history: Whether to summarize conversation history
        
    Returns:
        The conversation ID for continuing the conversation
    """
    url = f"http://{host}:{port}/api/chat"
    
    # Prepare the request payload
    payload = {
        "model": model,
        "message": message,
        "summarize_history": summarize_history
    }
    
    if conversation_id:
        payload["conversation_session_id"] = conversation_id
        
    if system_prompt:
        payload["system_prompt"] = system_prompt
    
    try:
        # Make the request with stream=True to get the response as it comes
        print_colored("\nSending request to chat endpoint...", "blue")
        start_time = time.time()
        
        response = requests.post(url, json=payload, stream=True)
        
        if response.status_code != 200:
            print_colored(f"Error: {response.status_code} - {response.text}", "red")
            return None
        
        # Process the streaming response
        print_colored("\nResponse:", "green")
        print_colored("=" * 50, "green")
        
        full_content = ""
        returned_conversation_id = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    
                    if data.get("error"):
                        print_colored(f"Error: {data['error']}", "red")
                        break
                    
                    content = data.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_content += content
                    
                    if data.get("done", False):
                        returned_conversation_id = data.get("conversation_id")
                        break
        
        elapsed_time = time.time() - start_time
        print("\n")
        print_colored("=" * 50, "green")
        print_colored(f"Response completed in {elapsed_time:.2f} seconds", "blue")
        
        if returned_conversation_id:
            print_colored(f"Conversation ID: {returned_conversation_id}", "blue")
            return returned_conversation_id
        
    except Exception as e:
        print_colored(f"Error: {str(e)}", "red")
    
    return None


def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Demo for chat endpoint")
    parser.add_argument("--host", type=str, default="localhost", help="API server hostname")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--system-prompt", type=str, help="Optional system prompt")
    
    args = parser.parse_args()
    
    # Check if the API server is running
    try:
        response = requests.get(f"http://{args.host}:{args.port}/")
        if response.status_code != 200:
            print_colored(f"Warning: API server returned status code {response.status_code}", "yellow")
    except requests.exceptions.ConnectionError:
        print_colored(f"Error: Could not connect to API server at {args.host}:{args.port}", "red")
        print_colored("Make sure the server is running with: uvicorn main:app --reload", "yellow")
        return
    
    print_colored("=" * 50, "cyan")
    print_colored("Chat Endpoint Demo", "cyan")
    print_colored("=" * 50, "cyan")
    print_colored("This demo allows you to test the chat endpoint with gpt-4o-mini model.", "cyan")
    print_colored("You can continue the conversation with the same session ID.", "cyan")
    print_colored("Type 'exit' or 'quit' to end the demo.", "cyan")
    print_colored("=" * 50, "cyan")
    
    conversation_id = None
    
    while True:
        # Get user input
        if conversation_id:
            print_colored("\nContinuing conversation... (type 'new' for a new conversation)", "blue")
        else:
            print_colored("\nStarting a new conversation...", "blue")
        
        message = input("\nYour message: ")
        
        if message.lower() in ["exit", "quit"]:
            print_colored("Exiting demo...", "yellow")
            break
        
        if message.lower() == "new" and conversation_id:
            conversation_id = None
            print_colored("Starting a new conversation...", "blue")
            message = input("\nYour message: ")
        
        if not message:
            print_colored("Message cannot be empty. Please try again.", "yellow")
            continue
        
        # Send the message to the chat endpoint
        conversation_id = stream_chat(
            host=args.host,
            port=args.port,
            message=message,
            model="gpt-4o-mini",
            conversation_id=conversation_id,
            system_prompt=args.system_prompt
        )


if __name__ == "__main__":
    main()
