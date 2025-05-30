"""
Database configuration and initialization for the chatapp-v2-api.

This module provides SQLAlchemy setup for database connections,
supporting both PostgreSQL for production and SQLite for local development.
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from contextlib import contextmanager
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("chatapp-v2-api.db")

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()
POSTGRES_CONNECTION_STRING = os.environ.get("POSTGRES_CONNECTION_STRING", "")
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatapp-v2.db")

# SQLAlchemy convention for constraint naming
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Create database engine based on configuration
if DB_TYPE == "postgres":
    if not POSTGRES_CONNECTION_STRING:
        logger.warning("POSTGRES_CONNECTION_STRING is not set, defaulting to SQLite")
        DB_TYPE = "sqlite"
        engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", connect_args={"check_same_thread": False})
    else:
        logger.info("Using PostgreSQL database")
        engine = create_engine(POSTGRES_CONNECTION_STRING, pool_pre_ping=True)
else:
    logger.info("Using SQLite database")
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# Global variable for test mode
_TEST_MODE = False
_TEST_SESSION = None

def set_test_mode(enabled=True, test_session=None):
    """
    Enable or disable test mode.
    
    In test mode, get_db will return the test_session directly instead of
    yielding a session from a context manager.
    
    Args:
        enabled: Whether to enable test mode
        test_session: The session to return in test mode
    """
    global _TEST_MODE, _TEST_SESSION
    _TEST_MODE = enabled
    _TEST_SESSION = test_session

def get_db():
    """
    Dependency for database sessions.
    
    In normal mode, this creates a new session and yields it.
    In test mode, it yields the test session.
    
    Yields:
        Session: A SQLAlchemy session
    """
    # If in test mode, yield the test session
    if _TEST_MODE and _TEST_SESSION is not None:
        yield _TEST_SESSION
        return
        
    # Normal operation - create a new session each time
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    
    This should be called during application startup.
    """
    # Import all models here to ensure they are registered with the Base
    from database.models import ConversationModel, MessageModel
    
    logger.info(f"Initializing database (type: {DB_TYPE})")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
