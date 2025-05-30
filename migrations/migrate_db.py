#!/usr/bin/env python3
"""
Database migration script for adding first_user_message and first_assistant_message columns
to the conversations table and populating them with data from existing messages.

This script is database-agnostic and works with both SQLite and Azure SQL databases.
"""

import os
import sys
from typing import Dict, Any, List, Tuple
import argparse

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.db.db_wrapper import DatabaseWrapper


def migrate_database(db_type=None):
    """
    Migrate the database to add first_user_message and first_assistant_message columns
    to the conversations table and populate them with data from existing messages.
    
    Args:
        db_type: The database type to use ('sqlite' or 'azure_sql')
    """
    # Create a database wrapper instance
    db = DatabaseWrapper(db_type)
    
    print(f"Starting database migration for {db.db_type} database")
    
    # Check if the columns already exist
    if db.column_exists('conversations', 'first_user_message') and db.column_exists('conversations', 'first_assistant_message'):
        print("Columns already exist, no migration needed.")
        return
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        if db.db_type == "sqlite":
            # SQLite migration approach - create new table and swap
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
            
        elif db.db_type == "azure_sql":
            # Azure SQL migration approach - alter table
            print("Adding new columns to conversations table...")
            
            # Check if first_user_message column exists
            if not db.column_exists('conversations', 'first_user_message'):
                cursor.execute('''
                ALTER TABLE conversations
                ADD first_user_message NVARCHAR(100) NULL
                ''')
            
            # Check if first_assistant_message column exists
            if not db.column_exists('conversations', 'first_assistant_message'):
                cursor.execute('''
                ALTER TABLE conversations
                ADD first_assistant_message NVARCHAR(100) NULL
                ''')
            
            # Find and populate the first user and assistant messages
            print("Finding first messages for each conversation...")
            cursor.execute('''
            SELECT DISTINCT conversation_id FROM messages
            ''')
            rows = cursor.fetchall()
            
            # Extract conversation IDs based on database type
            if db.db_type == "sqlite":
                conversation_ids = [row[0] for row in rows]
            else:
                conversation_ids = [row.conversation_id for row in rows]
            
            for conversation_id in conversation_ids:
                # Find first user message
                cursor.execute('''
                SELECT TOP 1 content FROM messages
                WHERE conversation_id = ? AND role = 'user'
                ORDER BY created_at ASC
                ''', (conversation_id,))
                first_user_row = cursor.fetchone()
                
                # Find first assistant message
                cursor.execute('''
                SELECT TOP 1 content FROM messages
                WHERE conversation_id = ? AND role = 'assistant'
                ORDER BY created_at ASC
                ''', (conversation_id,))
                first_assistant_row = cursor.fetchone()
                
                # Update the table with the first messages
                if first_user_row:
                    # Extract content based on database type
                    if db.db_type == "sqlite":
                        first_user_message = first_user_row[0][:100]  # Truncate to 100 chars
                    else:
                        first_user_message = first_user_row.content[:100]  # Truncate to 100 chars
                    
                    cursor.execute('''
                    UPDATE conversations
                    SET first_user_message = ?
                    WHERE id = ?
                    ''', (first_user_message, conversation_id))
                
                if first_assistant_row:
                    # Extract content based on database type
                    if db.db_type == "sqlite":
                        first_assistant_message = first_assistant_row[0][:100]  # Truncate to 100 chars
                    else:
                        first_assistant_message = first_assistant_row.content[:100]  # Truncate to 100 chars
                    
                    cursor.execute('''
                    UPDATE conversations
                    SET first_assistant_message = ?
                    WHERE id = ?
                    ''', (first_assistant_message, conversation_id))
        
        # Commit the changes
        conn.commit()
        
        print("Migration completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument("--db-type", choices=["sqlite", "azure_sql"], 
                        help="Database type to use (sqlite or azure_sql). Defaults to DB_TYPE environment variable or sqlite.")
    args = parser.parse_args()
    
    migrate_database(args.db_type)
