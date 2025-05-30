"""
CRUD operations for the chatapp-v2-api.

This module provides functions for creating, reading, updating, and deleting
data from the database using SQLAlchemy ORM.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import ConversationModel, MessageModel

# Configure logging
logger = logging.getLogger("chatapp-v2-api.db.crud")


# Conversation CRUD operations
def create_conversation(
    db: Session,
    title: str,
    model: str,
    user_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ConversationModel:
    """
    Create a new conversation.
    
    Args:
        db: Database session
        title: Conversation title
        model: LLM model used
        user_id: Optional user identifier
        system_prompt: Optional system instructions
        metadata: Optional metadata
        
    Returns:
        ConversationModel: The created conversation
    """
    conversation_id = str(uuid.uuid4())
    conversation = ConversationModel(
        id=conversation_id,
        title=title,
        model=model,
        user_id=user_id,
        system_prompt=system_prompt,
        _metadata=json.dumps(metadata) if metadata else None
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    logger.info(f"Created conversation with ID: {conversation_id}")
    return conversation


def get_conversation(
    db: Session,
    conversation_id: str,
    include_messages: bool = True
) -> Optional[ConversationModel]:
    """
    Get a conversation by ID.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        include_messages: Whether to include messages in the result
        
    Returns:
        ConversationModel: The conversation or None if not found
    """
    query = db.query(ConversationModel).filter(ConversationModel.id == conversation_id)
    
    if include_messages:
        conversation = query.first()
        if conversation:
            # Messages are loaded via the relationship
            return conversation
    else:
        return query.first()
    
    return None


def get_all_conversations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None
) -> List[ConversationModel]:
    """
    Get all conversations with optional pagination and filtering.
    
    Args:
        db: Database session
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        user_id: Optional user ID to filter by
        
    Returns:
        List[ConversationModel]: List of conversations
    """
    query = db.query(ConversationModel).order_by(desc(ConversationModel.updated_at))
    
    if user_id:
        query = query.filter(ConversationModel.user_id == user_id)
    
    return query.offset(skip).limit(limit).all()


def update_conversation(
    db: Session,
    conversation_id: str,
    title: Optional[str] = None,
    system_prompt: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[ConversationModel]:
    """
    Update a conversation.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        title: Optional new title
        system_prompt: Optional new system prompt
        metadata: Optional new metadata
        
    Returns:
        ConversationModel: The updated conversation or None if not found
    """
    conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    
    if conversation:
        if title is not None:
            conversation.title = title
        if system_prompt is not None:
            conversation.system_prompt = system_prompt
        if metadata is not None:
            conversation._metadata = json.dumps(metadata)
        
        conversation.updated_at = datetime.now()
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"Updated conversation with ID: {conversation_id}")
        return conversation
    
    return None


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        
    Returns:
        bool: True if the conversation was deleted, False otherwise
    """
    conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    
    if conversation:
        db.delete(conversation)
        db.commit()
        
        logger.info(f"Deleted conversation with ID: {conversation_id}")
        return True
    
    return False


# Message CRUD operations
def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    tokens: Optional[int] = None,
    model: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[MessageModel]:
    """
    Add a message to a conversation.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        role: Message role (user, assistant, system)
        content: Message content
        tokens: Optional token count
        model: Optional model override
        metadata: Optional metadata
        
    Returns:
        MessageModel: The created message or None if the conversation doesn't exist
    """
    # Check if conversation exists
    conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    
    if not conversation:
        logger.warning(f"Attempted to add message to non-existent conversation: {conversation_id}")
        return None
    
    # Create the message
    message_id = str(uuid.uuid4())
    message = MessageModel(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        tokens=tokens,
        model=model,
        _metadata=json.dumps(metadata) if metadata else None
    )
    
    db.add(message)
    
    # Update conversation's updated_at timestamp
    conversation.updated_at = datetime.now()
    
    # Update preview columns if this is the first message of its role type
    truncated_content = content[:100] if content else ""
    
    if role == "user" and not conversation.first_user_message:
        conversation.first_user_message = truncated_content
    elif role == "assistant" and not conversation.first_assistant_message:
        conversation.first_assistant_message = truncated_content
    
    db.commit()
    db.refresh(message)
    
    logger.info(f"Added message with ID: {message_id} to conversation: {conversation_id}")
    return message


def get_messages_by_conversation(
    db: Session,
    conversation_id: str,
    skip: int = 0,
    limit: Optional[int] = None
) -> List[MessageModel]:
    """
    Get all messages for a conversation with optional pagination.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        skip: Number of messages to skip
        limit: Maximum number of messages to return
        
    Returns:
        List[MessageModel]: List of messages
    """
    query = db.query(MessageModel).filter(
        MessageModel.conversation_id == conversation_id
    ).order_by(MessageModel.created_at)
    
    if skip:
        query = query.offset(skip)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_message_history(
    db: Session,
    conversation_id: str,
    summarize: bool = True,
    threshold: int = 20
) -> List[Dict[str, Any]]:
    """
    Get message history for a conversation, with optional summarization for long conversations.
    
    This is similar to the function in the LLM service provider, but works directly with the database.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        summarize: Whether to summarize long conversations
        threshold: Number of messages before summarization is applied
        
    Returns:
        List[Dict[str, Any]]: List of messages in the format expected by LLM providers
    """
    # Get the conversation with all messages
    conversation = get_conversation(db, conversation_id)
    
    if not conversation:
        logger.warning(f"Conversation not found: {conversation_id}")
        return []
    
    # Convert SQLAlchemy models to dictionaries
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
        if msg.role in ["user", "assistant", "system"]
    ]
    
    # Add system prompt if present
    if conversation.system_prompt and not any(msg["role"] == "system" for msg in messages):
        messages.insert(0, {"role": "system", "content": conversation.system_prompt})
    
    # If summarization is not needed or disabled, return all messages
    if not summarize or len(messages) <= threshold:
        return messages
    
    # For summarization, we would need to call the LLM service
    # This would typically be handled by the LLM service provider
    # For now, we'll just return a placeholder for the summarized messages
    
    # Keep the most recent messages (threshold - 1 to leave room for summary)
    recent_messages = messages[-(threshold - 1):]
    
    # Add a placeholder for the summary
    summary_message = {
        "role": "system",
        "content": f"[This would be a summary of {len(messages) - len(recent_messages)} earlier messages]"
    }
    
    # Return the summary followed by recent messages
    return [summary_message] + recent_messages
