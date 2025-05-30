"""
Database migration utilities for the chatapp-v2-api.

This module provides functions to help with database migrations using Alembic.
"""

import os
import logging
import argparse
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from database.database import Base, engine, get_db
from database.models import ConversationModel, MessageModel

# Configure logging
logger = logging.getLogger("chatapp-v2-api.db.migrations")


def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    
    This should be called during application startup.
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_tables():
    """
    Check if the database tables exist and print their structure.
    """
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    if not table_names:
        logger.warning("No tables found in the database")
        return
    
    logger.info(f"Found {len(table_names)} tables: {', '.join(table_names)}")
    
    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        logger.info(f"Table: {table_name}")
        for column in columns:
            logger.info(f"  - {column['name']}: {column['type']}")


def migrate_from_sqlite(sqlite_path, session):
    """
    Migrate data from SQLite database to the current database.
    
    Args:
        sqlite_path: Path to the SQLite database file
        session: SQLAlchemy session for the target database
    """
    import sqlite3
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database file not found: {sqlite_path}")
        return False
    
    logger.info(f"Migrating data from SQLite database: {sqlite_path}")
    
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        # Migrate conversations
        logger.info("Migrating conversations...")
        cursor = sqlite_conn.execute("SELECT * FROM conversations")
        rows = cursor.fetchall()
        
        for row in rows:
            # Convert row to dictionary
            conv_data = {key: row[key] for key in row.keys()}
            
            # Handle metadata (convert from JSON string if needed)
            if "metadata" in conv_data and conv_data["metadata"]:
                import json
                try:
                    metadata = json.loads(conv_data["metadata"])
                    conv_data["metadata"] = metadata
                except json.JSONDecodeError:
                    conv_data["metadata"] = {}
            
            # Create conversation model
            conversation = ConversationModel(
                id=conv_data["id"],
                title=conv_data["title"],
                created_at=conv_data["created_at"],
                updated_at=conv_data["updated_at"],
                user_id=conv_data["user_id"],
                model=conv_data["model"],
                system_prompt=conv_data["system_prompt"],
                first_user_message=conv_data.get("first_user_message"),
                first_assistant_message=conv_data.get("first_assistant_message"),
                _metadata=conv_data.get("metadata")
            )
            
            session.add(conversation)
        
        # Migrate messages
        logger.info("Migrating messages...")
        cursor = sqlite_conn.execute("SELECT * FROM messages")
        rows = cursor.fetchall()
        
        for row in rows:
            # Convert row to dictionary
            msg_data = {key: row[key] for key in row.keys()}
            
            # Handle metadata (convert from JSON string if needed)
            if "metadata" in msg_data and msg_data["metadata"]:
                import json
                try:
                    metadata = json.loads(msg_data["metadata"])
                    msg_data["metadata"] = metadata
                except json.JSONDecodeError:
                    msg_data["metadata"] = {}
            
            # Create message model
            message = MessageModel(
                id=msg_data["id"],
                conversation_id=msg_data["conversation_id"],
                role=msg_data["role"],
                content=msg_data["content"],
                created_at=msg_data["created_at"],
                tokens=msg_data["tokens"],
                model=msg_data["model"],
                _metadata=msg_data.get("metadata")
            )
            
            session.add(message)
        
        # Commit changes
        session.commit()
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error during migration: {e}")
        return False
    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Database migration utilities")
    parser.add_argument("--init", action="store_true", help="Initialize the database")
    parser.add_argument("--check", action="store_true", help="Check database tables")
    parser.add_argument("--migrate-sqlite", help="Migrate data from SQLite database")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if args.init:
        init_db()
    
    if args.check:
        check_db_tables()
    
    if args.migrate_sqlite:
        # Create a session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            migrate_from_sqlite(args.migrate_sqlite, session)
        finally:
            session.close()
