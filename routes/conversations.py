from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from database.database import get_db
from database.crud import get_all_conversations, get_conversation, delete_conversation
from schema.conversations import Conversation, ConversationSummary, DeleteResponse

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(user_id: Optional[str] = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """
    Get all conversations for a specific user.
    
    Args:
        user_id: User ID to filter conversations by (required)
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
        
    Returns:
        A list of conversation summary objects
    """
    # Debug: Print parameters
    print(f"\nlist_conversations called with user_id={user_id}, limit={limit}, offset={offset}")
    
    conversations = get_all_conversations(db=db, user_id=user_id, limit=limit, skip=offset)
    
    # Debug: Print conversations
    print(f"Got {len(conversations)} conversations from get_all_conversations")
    if conversations:
        print(f"First conversation type: {type(conversations[0])}")
        if hasattr(conversations[0], 'to_dict'):
            print("Has to_dict method")
        else:
            print(f"Keys: {conversations[0].keys() if isinstance(conversations[0], dict) else 'Not a dict'}")
    
    # Handle both SQLAlchemy models and dictionaries (for tests)
    result = []
    for i, conv in enumerate(conversations):
        try:
            if hasattr(conv, 'to_dict'):
                # SQLAlchemy model
                print(f"Processing SQLAlchemy model {i}")
                conv_dict = conv.to_dict()
                # Add message_count field (required by ConversationSummary model)
                conv_dict["message_count"] = len(conv.messages) if hasattr(conv, 'messages') else 0
                result.append(ConversationSummary.model_validate(conv_dict))
            else:
                # Dictionary (for tests)
                print(f"Processing dictionary {i}")
                # Ensure message_count field exists
                if "message_count" not in conv:
                    conv["message_count"] = 0
                # Debug: Print validation attempt
                print(f"Attempting to validate: {list(conv.keys())}")
                validated = ConversationSummary.model_validate(conv)
                print(f"Validation successful for {i}")
                result.append(validated)
        except Exception as e:
            print(f"Error processing conversation {i}: {str(e)}")
    
    # Debug: Print result
    print(f"Returning {len(result)} conversations")
    
    return result


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation_by_id(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get a conversation by ID, including all its messages.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        
    Returns:
        The conversation object with messages
        
    Raises:
        HTTPException: If the conversation is not found
    """
    conversation = get_conversation(db=db, conversation_id=conversation_id, include_messages=True)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Handle both SQLAlchemy models and dictionaries (for tests)
    if hasattr(conversation, 'to_dict'):
        # SQLAlchemy model
        conv_dict = conversation.to_dict()
        # Add messages to the dictionary
        if hasattr(conversation, 'messages'):
            conv_dict["messages"] = [msg.to_dict() if hasattr(msg, 'to_dict') else msg for msg in conversation.messages]
            # Add message_count field
            conv_dict["message_count"] = len(conversation.messages)
        else:
            conv_dict["message_count"] = 0
    else:
        # Dictionary (for tests)
        conv_dict = conversation
        # Ensure messages key exists
        if "messages" not in conv_dict:
            conv_dict["messages"] = []
        # Ensure message_count field exists
        if "message_count" not in conv_dict:
            conv_dict["message_count"] = len(conv_dict["messages"])
    
    return Conversation.model_validate(conv_dict)


@router.delete("/conversations/{conversation_id}", response_model=DeleteResponse)
async def delete_conversation_by_id(conversation_id: str, db: Session = Depends(get_db)):
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
    conversation = get_conversation(db=db, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete the conversation
    success = delete_conversation(db=db, conversation_id=conversation_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
    
    return {"message": f"Conversation {conversation_id} deleted successfully"}
