"""
Database configuration and initialization for the chatapp-v2-api.

This module provides SQLAlchemy setup for database connections,
supporting both PostgreSQL for production and SQLite for local development.
"""

import os
import logging
import urllib.parse
from sqlalchemy import create_engine, MetaData        
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chatapp-v2-api.db")

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE").lower()
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatapp-v2.db")
SUPABASE_USER = os.getenv("SUPABASE_USER", "")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "")
SUPABASE_HOST = os.getenv("SUPABASE_HOST", "")
SUPABASE_PORT = os.getenv("SUPABASE_PORT", "5432")
SUPABASE_DBNAME = os.getenv("SUPABASE_DBNAME", "")

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
# Determine which database engine to use
if DB_TYPE == "postgres":
    # Validate PostgreSQL connection parameters
    logger.info(f"PostgreSQL connection parameters: USER={SUPABASE_USER}, HOST={SUPABASE_HOST}, PORT={SUPABASE_PORT}, DB={SUPABASE_DBNAME}")
    if not all([SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_HOST, SUPABASE_DBNAME]):
        logger.warning("Missing required PostgreSQL connection parameters")
        logger.warning("Defaulting to SQLite")
        DB_TYPE = "sqlite"
    else:
        try:
            logger.info("Connecting to PostgreSQL database")
            # Create PostgreSQL connection string with proper URL encoding for special characters
            db_url = f"postgresql+psycopg2://{urllib.parse.quote_plus(SUPABASE_USER)}:{urllib.parse.quote_plus(SUPABASE_PASSWORD)}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DBNAME}?sslmode=require"
            
            # Create engine with PostgreSQL connection
            engine = create_engine(db_url, pool_pre_ping=True, echo=True)
            logger.info("Engine created successfully")
            
            # Test the connection
            with engine.connect() as conn:
                result = conn.execute(sa.text("SELECT 1")).fetchone()
                logger.info(f"Connection test result: [OK]")
                
            logger.info("PostgreSQL connection established successfully")
        except Exception as e:
            logger.info(f"Connection test result: [FAILED]")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Defaulting to SQLite")
            DB_TYPE = "sqlite"

# If we're not using PostgreSQL, use SQLite
if DB_TYPE != "postgres":
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
    logger.info(f"Initializing database (type: {DB_TYPE})")
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
