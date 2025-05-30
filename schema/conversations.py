from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime


class Message(BaseModel):
    """Pydantic model for a message in a conversation."""
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    tokens: Optional[int] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)  # For compatibility with SQLAlchemy ORM models


class MessageCreate(BaseModel):
    """Pydantic model for creating a new message."""
    role: str
    content: str
    tokens: Optional[int] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationBase(BaseModel):
    """Base Pydantic model for conversation data."""
    title: str
    model: str
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """Pydantic model for creating a new conversation."""
    pass


class Conversation(ConversationBase):
    """Pydantic model for a conversation with all its details."""
    id: str
    created_at: datetime
    updated_at: datetime
    first_user_message: Optional[str] = None
    first_assistant_message: Optional[str] = None
    messages: List[Message] = []
    message_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)  # For compatibility with SQLAlchemy ORM models


class ConversationSummary(BaseModel):
    """Pydantic model for a conversation summary (without messages)."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None
    first_user_message: Optional[str] = None
    first_assistant_message: Optional[str] = None
    message_count: int
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)  # For compatibility with SQLAlchemy ORM models


class DeleteResponse(BaseModel):
    """Pydantic model for a delete operation response."""
    message: str
