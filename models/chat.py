from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    """Pydantic model for chat requests."""
    model: str
    message: str
    conversation_session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    summarize_history: Optional[bool] = True
    title: Optional[str] = None  # Optional title for new conversations


class ChatStreamResponse(BaseModel):
    """Pydantic model for chat stream response chunks."""
    content: str = ""
    done: bool = False
    conversation_id: Optional[str] = None
    error: Optional[str] = None
