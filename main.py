from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatapp-v2-api")

# Load environment variables
load_dotenv()

# Import database wrapper
from migrations.db.db_wrapper import init_db, db_wrapper, DatabaseWrapper

# Import database operations from factory
from migrations.db.db_factory import (
    get_db_type,
    create_conversation,
    add_message,
    get_conversation,
    get_all_conversations,
    delete_conversation
)

# Import LLM service wrapper
from llm_service_providers.index import llm_service
from misc.constants import DEFAULT_MODELS, Provider

# Import routers
from routes.chat import router as chat_router
from routes.models import router as models_router
from routes.conversations import router as conversations_router

# Define lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    try:
        # Use the global db_wrapper instance that was already configured
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.warning("Application will continue but database functionality may be limited")
    
    yield
    # Shutdown: Clean up resources if needed
    logger.info("Shutting down application")

# Create FastAPI app with lifespan
app = FastAPI(
    title="ChatApp v2 API",
    description="API for ChatApp v2 with multiple LLM providers",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(models_router, prefix="/api", tags=["models"])
app.include_router(conversations_router, prefix="/api", tags=["conversations"])

# The database initialization is now handled in the lifespan context manager


@app.get("/")
async def root():
    return {"message": "Welcome to ChatApp v2 API"}


# Root endpoint remains in main.py