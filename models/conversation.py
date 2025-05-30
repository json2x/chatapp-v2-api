"""
Conversation model for the database.
This model represents the conversations table in the database.
"""

from pydantic import Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import json

from models.base import BaseDBModel


class Conversation(BaseDBModel):
    """
    Database model for the conversations table that matches the SQLite schema.
    
    Table schema:
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
    """
    title: str
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None
    first_user_message: Optional[str] = None
    first_assistant_message: Optional[str] = None
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
