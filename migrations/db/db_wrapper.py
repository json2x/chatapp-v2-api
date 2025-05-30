"""
Database wrapper for the chatapp-v2-api.

This module provides a database abstraction layer to support multiple database backends
including SQLite and Azure SQL Server via ODBC.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
import uuid
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("chatapp-v2-api.db")

# Import pyodbc only when needed to avoid errors if ODBC drivers aren't installed
pyodbc = None

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()  # Default to SQLite if not specified
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatapp-v2.db")

# Function to get Azure SQL connection string from environment variable
def get_azure_sql_connection_string():
    """Get the Azure SQL connection string from the environment variable"""
    connection_string = os.environ.get("AZURE_SQL_CONNECTION_STRING", "")
    
    if not connection_string:
        raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set or empty")
    
    return connection_string


class DatabaseWrapper:
    """
    Database wrapper class that provides a unified interface for different database backends.
    """
    
    def __init__(self, db_type=None):
        """
        Initialize the database wrapper.
        
        Args:
            db_type: The database type to use ('sqlite' or 'azure_sql')
        """
        self.db_type = db_type or DB_TYPE
        
        # Validate database type
        if self.db_type not in ["sqlite", "azure_sql"]:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        # Validate Azure SQL configuration if selected
        if self.db_type == "azure_sql":
            connection_string = os.environ.get("AZURE_SQL_CONNECTION_STRING", "")
            if not connection_string or connection_string.strip() == "":
                logger.warning("AZURE_SQL_CONNECTION_STRING is empty, defaulting to SQLite")
                self.db_type = "sqlite"
        
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            Connection: A database connection with appropriate row factory
        """
        if self.db_type == "sqlite":
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
        elif self.db_type == "azure_sql":
            # Import pyodbc only when needed
            global pyodbc
            if pyodbc is None:
                try:
                    import pyodbc
                except ImportError:
                    raise ImportError(
                        "pyodbc module is required for Azure SQL connections. "
                        "Please install it with 'pip install pyodbc' and ensure "
                        "that the ODBC driver for SQL Server is installed."
                    )
            
            try:
                # Get the connection string from environment variables
                connection_string = get_azure_sql_connection_string()
                
                # Try to establish the connection
                conn = pyodbc.connect(connection_string)
                try:
                    yield conn
                finally:
                    conn.close()
            except pyodbc.Error as e:
                # Provide more detailed error information for connection issues
                error_msg = str(e)
                if "DSN" in error_msg or "driver" in error_msg.lower():
                    raise ConnectionError(
                        f"ODBC Driver error: {error_msg}. "
                        "Please ensure the ODBC Driver for SQL Server is installed. "
                        "On macOS, you can install it with 'brew install unixodbc'."
                    )
                elif "connection" in error_msg.lower() or "server" in error_msg.lower():
                    raise ConnectionError(
                        f"Cannot connect to Azure SQL Server: {error_msg}. "
                        "Please check your server address, firewall settings, and network connection."
                    )
                elif "login" in error_msg.lower() or "password" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise ConnectionError(
                        f"Authentication failed: {error_msg}. "
                        "Please check your username and password."
                    )
                else:
                    raise ConnectionError(f"Azure SQL connection error: {error_msg}")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def execute_query(self, query, params=None):
        """
        Execute a query and return all results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of rows as dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            
            if self.db_type == "sqlite":
                # SQLite's Row objects can be directly converted to dict
                rows = [dict(row) for row in cursor.fetchall()]
            else:
                # For other databases, manually convert to dict
                columns = [column[0] for column in cursor.description] if cursor.description else []
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return rows
    
    def execute_non_query(self, query, params=None):
        """
        Execute a non-query statement (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            affected = cursor.rowcount
            conn.commit()
            return affected
    
    def get_table_info(self, table_name):
        """
        Get information about table columns.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information
        """
        if self.db_type == "sqlite":
            return self.execute_query(f"PRAGMA table_info({table_name})")
        elif self.db_type == "azure_sql":
            query = """
            SELECT 
                c.name AS name,
                t.name AS type,
                c.is_nullable AS nullable,
                CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END AS pk
            FROM 
                sys.columns c
            JOIN 
                sys.types t ON c.user_type_id = t.user_type_id
            LEFT JOIN 
                sys.index_columns ic ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            LEFT JOIN 
                sys.indexes pk ON pk.object_id = ic.object_id AND pk.index_id = ic.index_id AND pk.is_primary_key = 1
            WHERE 
                c.object_id = OBJECT_ID(?)
            """
            return self.execute_query(query, [table_name])
    
    def table_exists(self, table_name):
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        if self.db_type == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, [table_name])
            return len(result) > 0
        elif self.db_type == "azure_sql":
            query = "SELECT OBJECT_ID(?) AS object_id"
            result = self.execute_query(query, [table_name])
            return result and result[0].get('object_id') is not None
    
    def column_exists(self, table_name, column_name):
        """
        Check if a column exists in a table.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            bool: True if the column exists, False otherwise
        """
        columns = self.get_table_info(table_name)
        
        if self.db_type == "sqlite":
            return any(col['name'] == column_name for col in columns)
        elif self.db_type == "azure_sql":
            return any(col['name'] == column_name for col in columns)
    
    def adapt_query_for_db(self, query):
        """
        Adapt a query for the specific database type.
        
        Args:
            query: The SQL query to adapt
            
        Returns:
            str: The adapted query
        """
        if self.db_type == "sqlite":
            return query
        elif self.db_type == "azure_sql":
            # Replace SQLite-specific syntax with T-SQL equivalents
            # Replace datetime('now') with GETDATE()
            query = query.replace("datetime('now')", "GETDATE()")
            
            # Replace ? placeholders with @p1, @p2, etc. for ODBC
            placeholder_count = query.count('?')
            for i in range(placeholder_count, 0, -1):
                query = query.replace('?', f'@p{i}', 1)
                
            return query


# Create a default instance based on the environment variable
db_wrapper = DatabaseWrapper(DB_TYPE)


def init_db(wrapper=None):
    """
    Initialize the database by creating necessary tables if they don't exist.
    
    Args:
        wrapper: Optional database wrapper instance. If not provided, the default instance will be used.
    """
    wrapper = wrapper or db_wrapper
    
    # Simply report which database is being initialized
    logger.info(f"Initializing database (type: {wrapper.db_type})")
    
    with wrapper.get_connection() as conn:
        cursor = conn.cursor()
        
        if wrapper.db_type == "sqlite":
            # Create conversations table for SQLite
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
            
            # Create messages table for SQLite
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
            
        elif wrapper.db_type == "azure_sql":
            # Create conversations table for Azure SQL
            if not wrapper.table_exists('conversations'):
                cursor.execute('''
                CREATE TABLE conversations (
                    id NVARCHAR(36) PRIMARY KEY,
                    title NVARCHAR(255) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
                    user_id NVARCHAR(255),
                    model NVARCHAR(255) NOT NULL,
                    system_prompt NVARCHAR(MAX),
                    first_user_message NVARCHAR(100),
                    first_assistant_message NVARCHAR(100),
                    metadata NVARCHAR(MAX)
                )
                ''')
            
            # Create messages table for Azure SQL
            if not wrapper.table_exists('messages'):
                cursor.execute('''
                CREATE TABLE messages (
                    id NVARCHAR(36) PRIMARY KEY,
                    conversation_id NVARCHAR(36) NOT NULL,
                    role NVARCHAR(50) NOT NULL,
                    content NVARCHAR(MAX) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    tokens INT,
                    model NVARCHAR(255),
                    metadata NVARCHAR(MAX),
                    CONSTRAINT FK_messages_conversation_id FOREIGN KEY (conversation_id) 
                    REFERENCES conversations (id) ON DELETE CASCADE
                )
                ''')
                
                # Create index for faster queries
                cursor.execute('CREATE INDEX idx_messages_conversation_id ON messages (conversation_id)')
        
        conn.commit()


# Don't automatically initialize the database when imported
# This will be done explicitly in the application startup
