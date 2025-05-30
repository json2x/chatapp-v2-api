from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from migrations.db.db_factory import get_all_conversations, get_conversation, delete_conversation
from schema.conversations import Conversation, ConversationSummary, DeleteResponse

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(user_id: str, limit: int = 100, offset: int = 0):
    """
    Get all conversations for a specific user.
    
    Args:
        user_id: User ID to filter conversations by (required)
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
        
    Returns:
        A list of conversation summary objects
    """
    return get_all_conversations(user_id=user_id, limit=limit, offset=offset)


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation_by_id(conversation_id: str):
    """
    Get a conversation by ID, including all its messages.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        
    Returns:
        The conversation object with messages
        
    Raises:
        HTTPException: If the conversation is not found
    """
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", response_model=DeleteResponse)
async def delete_conversation_by_id(conversation_id: str):
    """
    Delete a conversation by ID.
    
    Args:
        conversation_id: The ID of the conversation to delete
        
    Returns:
        A success message
        
    Raises:
        HTTPException: If the conversation is not found
    """
    # Check if the conversation exists first
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete the conversation
    delete_conversation(conversation_id)
    
    return {"message": f"Conversation {conversation_id} deleted successfully"}
