"""
SQLAlchemy models for the chatapp-v2-api.

This module defines the database tables using SQLAlchemy ORM.
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from database.database import Base


class ConversationModel(Base):
    """
    SQLAlchemy model for the conversations table.
    """
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    user_id = Column(String(255), nullable=True)
    model = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    first_user_message = Column(String(100), nullable=True)
    first_assistant_message = Column(String(100), nullable=True)
    _metadata = Column("metadata", Text, nullable=True)
    
    # Define relationship with messages
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    
    @hybrid_property
    def metadata_dict(self):
        """Get metadata as a dictionary."""
        if self._metadata:
            try:
                return json.loads(self._metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value):
        """Set metadata from a dictionary."""
        if value is None:
            self._metadata = None
        elif isinstance(value, dict):
            self._metadata = json.dumps(value)
        else:
            self._metadata = value
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "first_user_message": self.first_user_message,
            "first_assistant_message": self.first_assistant_message,
            "metadata": self.metadata_dict
        }


class MessageModel(Base):
    """
    SQLAlchemy model for the messages table.
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    tokens = Column(Integer, nullable=True)
    model = Column(String(255), nullable=True)
    _metadata = Column("metadata", Text, nullable=True)
    
    # Define relationship with conversation
    conversation = relationship("ConversationModel", back_populates="messages")
    
    # Create index for faster queries
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
    )
    
    @hybrid_property
    def metadata_dict(self):
        """Get metadata as a dictionary."""
        if self._metadata:
            try:
                return json.loads(self._metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value):
        """Set metadata from a dictionary."""
        if value is None:
            self._metadata = None
        elif isinstance(value, dict):
            self._metadata = json.dumps(value)
        else:
            self._metadata = value
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tokens": self.tokens,
            "model": self.model,
            "metadata": self.metadata_dict
        }
