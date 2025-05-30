#!/usr/bin/env python3
"""
Test script for the database wrapper.

This script tests both SQLite and Azure SQL database implementations
by creating a conversation, adding messages, and retrieving them.
"""

import os
import sys
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.db.db_wrapper import DatabaseWrapper, init_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_database(db_type):
    """
    Test database operations with the specified database type.
    
    Args:
        db_type: The database type to test ('sqlite' or 'azure_sql')
    """
    print(f"\n=== Testing {db_type} database ===\n")
    
    # Set environment variable for database type
    os.environ["DB_TYPE"] = db_type
    
    try:
        # Create database wrapper with the specified type
        print(f"Creating database wrapper for {db_type}...")
        db = DatabaseWrapper(db_type)
        
        # Initialize database
        print("Initializing database...")
        init_db(db)
        
        print(f"Successfully initialized {db_type} database")
    except Exception as e:
        print(f"Error initializing {db_type} database: {e}")
        print(f"Test failed for {db_type} database.")
        return
    
    # Import database operations from factory
    # We import here to ensure the DB_TYPE environment variable is set
    from migrations.db.db_factory import (
        create_conversation,
        add_message,
        get_conversation,
        get_all_conversations,
        delete_conversation
    )
    
    # Create a test conversation
    print("Creating test conversation...")
    conversation_id = create_conversation(
        title=f"Test Conversation ({db_type})",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant.",
        metadata={"test": True, "db_type": db_type}
    )
    print(f"Created conversation with ID: {conversation_id}")
    
    # Add user message
    print("Adding user message...")
    user_message_id = add_message(
        conversation_id=conversation_id,
        role="user",
        content=f"Hello, this is a test message from {db_type} database test.",
        metadata={"timestamp": str(datetime.now())}
    )
    print(f"Added user message with ID: {user_message_id}")
    
    # Add assistant message
    print("Adding assistant message...")
    assistant_message_id = add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=f"Hello! I'm responding to your test message in the {db_type} database.",
        tokens=25,
        metadata={"timestamp": str(datetime.now())}
    )
    print(f"Added assistant message with ID: {assistant_message_id}")
    
    # Get the conversation
    print("Retrieving conversation...")
    conversation = get_conversation(conversation_id)
    print(f"Retrieved conversation: {conversation['title']}")
    print(f"First user message preview: {conversation['first_user_message']}")
    print(f"First assistant message preview: {conversation['first_assistant_message']}")
    print(f"Number of messages: {len(conversation['messages'])}")
    
    # List all conversations
    print("Listing all conversations...")
    conversations = get_all_conversations(limit=5)
    print(f"Found {len(conversations)} conversations")
    
    # Clean up (optional)
    if input("Delete test conversation? (y/n): ").lower() == 'y':
        print("Deleting test conversation...")
        deleted = delete_conversation(conversation_id)
        print(f"Conversation deleted: {deleted}")
    
    print(f"\n=== {db_type} database test completed ===\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test database wrapper")
    parser.add_argument("--db-type", choices=["sqlite", "azure_sql"], default="sqlite",
                        help="Database type to test (sqlite or azure_sql)")
    parser.add_argument("--both", action="store_true", help="Test both database types")
    args = parser.parse_args()
    
    if args.both:
        test_database("sqlite")
        test_database("azure_sql")
    else:
        test_database(args.db_type)
