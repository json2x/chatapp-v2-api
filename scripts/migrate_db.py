#!/usr/bin/env python3
"""
Database migration script for adding first_user_message and first_assistant_message columns
to the conversations table and populating them with data from existing messages.
"""

import os
import sys
import sqlite3
from typing import Dict, Any, List, Tuple

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from misc.db import DB_PATH, get_db_connection


def migrate_database():
    """
    Migrate the database to add first_user_message and first_assistant_message columns
    to the conversations table and populate them with data from existing messages.
    """
    print(f"Starting database migration for {DB_PATH}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'first_user_message' in columns and 'first_assistant_message' in columns:
            print("Columns already exist, no migration needed.")
            return
        
        print("Creating temporary table...")
        # Create a temporary table with the new schema
        cursor.execute('''
        CREATE TABLE conversations_new (
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
        
        # Copy data from the old table to the new one
        print("Copying data to new table...")
        cursor.execute('''
        INSERT INTO conversations_new (id, title, created_at, updated_at, user_id, model, system_prompt, metadata)
        SELECT id, title, created_at, updated_at, user_id, model, system_prompt, metadata FROM conversations
        ''')
        
        # Find and populate the first user and assistant messages
        print("Finding first messages for each conversation...")
        cursor.execute('''
        SELECT DISTINCT conversation_id FROM messages
        ''')
        conversation_ids = [row[0] for row in cursor.fetchall()]
        
        for conversation_id in conversation_ids:
            # Find first user message
            cursor.execute('''
            SELECT content FROM messages
            WHERE conversation_id = ? AND role = 'user'
            ORDER BY created_at ASC
            LIMIT 1
            ''', (conversation_id,))
            first_user_row = cursor.fetchone()
            
            # Find first assistant message
            cursor.execute('''
            SELECT content FROM messages
            WHERE conversation_id = ? AND role = 'assistant'
            ORDER BY created_at ASC
            LIMIT 1
            ''', (conversation_id,))
            first_assistant_row = cursor.fetchone()
            
            # Update the new table with the first messages
            if first_user_row:
                first_user_message = first_user_row[0][:100]  # Truncate to 100 chars
                cursor.execute('''
                UPDATE conversations_new
                SET first_user_message = ?
                WHERE id = ?
                ''', (first_user_message, conversation_id))
            
            if first_assistant_row:
                first_assistant_message = first_assistant_row[0][:100]  # Truncate to 100 chars
                cursor.execute('''
                UPDATE conversations_new
                SET first_assistant_message = ?
                WHERE id = ?
                ''', (first_assistant_message, conversation_id))
        
        # Replace the old table with the new one
        print("Replacing old table with new table...")
        cursor.execute('DROP TABLE conversations')
        cursor.execute('ALTER TABLE conversations_new RENAME TO conversations')
        
        # Commit the changes
        conn.commit()
        
        print("Migration completed successfully!")


if __name__ == "__main__":
    migrate_database()
