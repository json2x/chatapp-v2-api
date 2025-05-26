"""
Database utilities for the chatapp-v2-api.

This module provides database connection and operations for the chat application.
It initializes a SQLite database and defines the schema for conversation history.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
import uuid

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatapp-v2.db")


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: A database connection with row factory set to sqlite3.Row
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    Initialize the database by creating necessary tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            model TEXT NOT NULL,
            system_prompt TEXT,
            first_user_message TEXT,
            first_assistant_message TEXT,
            metadata TEXT
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tokens INTEGER,
            model TEXT,
            metadata TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)')
        
        conn.commit()


def create_conversation(title: str, model: str, system_prompt: Optional[str] = None, 
                       user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new conversation.
    
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
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO conversations (id, title, created_at, updated_at, user_id, model, system_prompt, first_user_message, first_assistant_message, metadata)
        VALUES (?, ?, datetime('now'), datetime('now'), ?, ?, ?, NULL, NULL, ?)
        ''', (
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
    Add a message to a conversation.
    
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
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Add the message
        cursor.execute('''
        INSERT INTO messages (id, conversation_id, role, content, created_at, tokens, model, metadata)
        VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
        ''', (
            message_id,
            conversation_id,
            role,
            content,
            tokens,
            model,
            json.dumps(metadata) if metadata else None
        ))
        
        # Check if this is the first message of this role for the conversation
        if role in ['user', 'assistant']:
            # The count will be 1 (not 0) because we just inserted the message above
            cursor.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE conversation_id = ? AND role = ?
            ''', (conversation_id, role))
            
            count = cursor.fetchone()[0]
            
            # If this is the first message of this role, update the corresponding column
            # The count will be 1 for the first message since we just inserted it
            if count == 1:
                # Truncate content to 100 characters if needed
                truncated_content = content[:100] if len(content) > 100 else content
                
                if role == 'user':
                    cursor.execute('''
                    UPDATE conversations
                    SET first_user_message = ?, updated_at = datetime('now')
                    WHERE id = ?
                    ''', (truncated_content, conversation_id))
                else:  # assistant
                    cursor.execute('''
                    UPDATE conversations
                    SET first_assistant_message = ?, updated_at = datetime('now')
                    WHERE id = ?
                    ''', (truncated_content, conversation_id))
            else:
                # Just update the timestamp if not the first message
                cursor.execute('''
                UPDATE conversations
                SET updated_at = datetime('now')
                WHERE id = ?
                ''', (conversation_id,))
        else:
            # For system messages or other roles, just update the timestamp
            cursor.execute('''
            UPDATE conversations
            SET updated_at = datetime('now')
            WHERE id = ?
            ''', (conversation_id,))
        
        conn.commit()
    
    return message_id


def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Get a conversation by ID, including all its messages.
    
    Args:
        conversation_id: The ID of the conversation
        
    Returns:
        Dict: The conversation with its messages
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        conversation_row = cursor.fetchone()
        
        if not conversation_row:
            return None
        
        conversation = dict(conversation_row)
        
        # Parse metadata if present
        if conversation['metadata']:
            conversation['metadata'] = json.loads(conversation['metadata'])
        
        # Get all messages for this conversation
        cursor.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at', (conversation_id,))
        message_rows = cursor.fetchall()
        
        messages = []
        for row in message_rows:
            message = dict(row)
            if message['metadata']:
                message['metadata'] = json.loads(message['metadata'])
            messages.append(message)
        
        conversation['messages'] = messages
        
        return conversation


def get_all_conversations(user_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all conversations, optionally filtered by user_id.
    
    Args:
        user_id: Optional user identifier to filter by
        limit: Maximum number of conversations to return
        offset: Offset for pagination
        
    Returns:
        List[Dict]: List of conversations
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = '''
        SELECT c.*, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        '''
        
        params = []
        if user_id:
            query += ' WHERE c.user_id = ?'
            params.append(user_id)
        
        query += ' GROUP BY c.id ORDER BY c.updated_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            conversation = dict(row)
            if conversation['metadata']:
                conversation['metadata'] = json.loads(conversation['metadata'])
            conversations.append(conversation)
        
        return conversations


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: The ID of the conversation to delete
        
    Returns:
        bool: True if the conversation was deleted, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        
        return deleted


# Initialize the database when this module is imported
init_db()
