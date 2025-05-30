"""
Azure SQL database utilities for the chatapp-v2-api.

This module provides database operations specifically for Azure SQL Server.
It uses the database wrapper to handle connections and operations.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import uuid
import pyodbc
from contextlib import contextmanager
from dotenv import load_dotenv

from migrations.db.db_wrapper import db_wrapper

# Load environment variables
load_dotenv()


def create_conversation(title: str, model: str, system_prompt: Optional[str] = None, 
                       user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new conversation in Azure SQL database.
    
    Args:
        title: The title of the conversation
        model: The model used for the conversation
        system_prompt: Optional system prompt for the conversation
        user_id: Optional user identifier
        metadata: Optional metadata as a dictionary
        
    Returns:
        str: The ID of the created conversation
    """
    conversation_id = str(uuid.uuid4())
    
    with db_wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        # Adapt query for Azure SQL
        query = """
        INSERT INTO conversations 
        (id, title, created_at, updated_at, user_id, model, system_prompt, first_user_message, first_assistant_message, metadata)
        VALUES (?, ?, GETDATE(), GETDATE(), ?, ?, ?, NULL, NULL, ?)
        """
        
        cursor.execute(query, (
            conversation_id,
            title,
            user_id,
            model,
            system_prompt,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
    
    return conversation_id


def add_message(conversation_id: str, role: str, content: str, 
               tokens: Optional[int] = None, model: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Add a message to a conversation in Azure SQL database.
    
    Args:
        conversation_id: The ID of the conversation
        role: The role of the message sender (e.g., 'user', 'assistant', 'system')
        content: The content of the message
        tokens: Optional token count
        model: Optional model used for this specific message
        metadata: Optional metadata as a dictionary
        
    Returns:
        str: The ID of the created message
    """
    message_id = str(uuid.uuid4())
    
    with db_wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        # Insert the message
        cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, created_at, tokens, model, metadata)
        VALUES (?, ?, ?, ?, GETDATE(), ?, ?, ?)
        """, (
            message_id,
            conversation_id,
            role,
            content,
            tokens,
            model,
            json.dumps(metadata) if metadata else None
        ))
        
        # Update the conversation's first messages if needed
        if role == 'user':
            # Check if this is the first user message
            cursor.execute("""
            SELECT first_user_message FROM conversations WHERE id = ?
            """, (conversation_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                # This is the first user message, update the conversation
                truncated_content = content[:100]  # Truncate to 100 characters
                cursor.execute("""
                UPDATE conversations
                SET first_user_message = ?, updated_at = GETDATE()
                WHERE id = ?
                """, (truncated_content, conversation_id))
            else:
                # Just update the timestamp
                cursor.execute("""
                UPDATE conversations
                SET updated_at = GETDATE()
                WHERE id = ?
                """, (conversation_id,))
                
        elif role == 'assistant':
            # Check if this is the first assistant message
            cursor.execute("""
            SELECT first_assistant_message FROM conversations WHERE id = ?
            """, (conversation_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                # This is the first assistant message, update the conversation
                truncated_content = content[:100]  # Truncate to 100 characters
                cursor.execute("""
                UPDATE conversations
                SET first_assistant_message = ?, updated_at = GETDATE()
                WHERE id = ?
                """, (truncated_content, conversation_id))
            else:
                # Just update the timestamp
                cursor.execute("""
                UPDATE conversations
                SET updated_at = GETDATE()
                WHERE id = ?
                """, (conversation_id,))
        else:
            # For system messages or other roles, just update the timestamp
            cursor.execute("""
            UPDATE conversations
            SET updated_at = GETDATE()
            WHERE id = ?
            """, (conversation_id,))
        
        conn.commit()
    
    return message_id


def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Get a conversation by ID from Azure SQL, including all its messages.
    
    Args:
        conversation_id: The ID of the conversation
        
    Returns:
        Dict: The conversation with its messages
    """
    with db_wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        conversation_row = cursor.fetchone()
        
        if not conversation_row:
            return None
        
        # Convert row to dictionary
        columns = [column[0] for column in cursor.description]
        conversation = dict(zip(columns, conversation_row))
        
        # Parse metadata if present
        if conversation['metadata']:
            conversation['metadata'] = json.loads(conversation['metadata'])
        
        # Get all messages for this conversation
        cursor.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at', (conversation_id,))
        message_rows = cursor.fetchall()
        
        messages = []
        for row in message_rows:
            # Convert row to dictionary
            columns = [column[0] for column in cursor.description]
            message = dict(zip(columns, row))
            
            if message['metadata']:
                message['metadata'] = json.loads(message['metadata'])
            messages.append(message)
        
        conversation['messages'] = messages
        
        return conversation


def get_all_conversations(user_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all conversations from Azure SQL, optionally filtered by user_id.
    
    Args:
        user_id: Optional user identifier to filter by
        limit: Maximum number of conversations to return
        offset: Offset for pagination
        
    Returns:
        List[Dict]: List of conversations
    """
    with db_wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
        FROM conversations c
        """
        
        params = []
        if user_id:
            query += ' WHERE c.user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY c.updated_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
        params.extend([offset, limit])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            # Convert row to dictionary
            columns = [column[0] for column in cursor.description]
            conversation = dict(zip(columns, row))
            
            if conversation['metadata']:
                conversation['metadata'] = json.loads(conversation['metadata'])
            conversations.append(conversation)
        
        return conversations


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages from Azure SQL.
    
    Args:
        conversation_id: The ID of the conversation to delete
        
    Returns:
        bool: True if the conversation was deleted, False otherwise
    """
    with db_wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        
        return deleted
