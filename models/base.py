"""
Base models for database entities.
These models provide common functionality for all database models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class BaseDBModel(BaseModel):
    """Base model for database models with common fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
