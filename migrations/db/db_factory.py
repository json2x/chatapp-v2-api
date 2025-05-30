"""
Database factory for the chatapp-v2-api.

This module provides a factory to select the appropriate database implementation
based on the configured database type.
"""

import os
from typing import Dict, List, Any, Optional, Union, Callable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database type from environment
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()

# Import database implementations
if DB_TYPE == "sqlite":
    # Import from the original location for now
    # This should be updated once the SQLite implementation is moved to migrations/db/
    from misc.db import (
        create_conversation as sqlite_create_conversation,
        add_message as sqlite_add_message,
        get_conversation as sqlite_get_conversation,
        get_all_conversations as sqlite_get_all_conversations,
        delete_conversation as sqlite_delete_conversation
    )
    
    # Use SQLite implementation
    create_conversation = sqlite_create_conversation
    add_message = sqlite_add_message
    get_conversation = sqlite_get_conversation
    get_all_conversations = sqlite_get_all_conversations
    delete_conversation = sqlite_delete_conversation
    
elif DB_TYPE == "azure_sql":
    from migrations.db.db_azure import (
        create_conversation as azure_create_conversation,
        add_message as azure_add_message,
        get_conversation as azure_get_conversation,
        get_all_conversations as azure_get_all_conversations,
        delete_conversation as azure_delete_conversation
    )
    
    # Use Azure SQL implementation
    create_conversation = azure_create_conversation
    add_message = azure_add_message
    get_conversation = azure_get_conversation
    get_all_conversations = azure_get_all_conversations
    delete_conversation = azure_delete_conversation
    
else:
    raise ValueError(f"Unsupported database type: {DB_TYPE}")


# Function to get the current database type
def get_db_type() -> str:
    """
    Get the current database type.
    
    Returns:
        str: The database type ('sqlite' or 'azure_sql')
    """
    return DB_TYPE
