"""
Message model for the database.
This model represents the messages table in the database.
"""

from pydantic import Field, field_validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import json

from models.base import BaseDBModel


class Message(BaseDBModel):
    """
    Database model for the messages table that matches the SQLite schema.
    
    Table schema:
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
    """
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    tokens: Optional[int] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, value):
        """Parse metadata from JSON string if it's a string."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value or {}
    
    def model_dump_json(self, **kwargs):
        """Convert model to JSON with metadata serialized."""
        data = self.model_dump(**kwargs)
        if isinstance(data.get('metadata'), dict):
            data['metadata'] = json.dumps(data['metadata'])
        return json.dumps(data)
