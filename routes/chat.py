from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List, Generator
import uuid
import json
import asyncio
from datetime import datetime

# Import database utilities
from migrations.db.db_factory import create_conversation, add_message, get_conversation
from llm_service_providers.index import llm_service

# Import models
from schema.chat import ChatRequest, ChatStreamResponse

router = APIRouter()

async def stream_generator(
    model: str,
    messages: List[Dict[str, str]],
    conversation_id: str
) -> Generator[str, None, None]:
    """
    Generate a stream of SSE events from the chat completion.
    
    Args:
        model: The model to use for the chat completion
        messages: The messages to send to the model
        conversation_id: The ID of the conversation
        
    Yields:
        SSE formatted response chunks
    """
    # Initialize variables to collect the full response
    full_content = ""
    
    try:
        # Get the streaming response from the LLM service
        for chunk in llm_service.stream_chat(model=model, messages=messages):
            # Extract content from the chunk (this may vary depending on the provider)
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                # OpenAI format
                delta = chunk.choices[0].delta
                content = delta.content if hasattr(delta, 'content') and delta.content else ""
            elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                # Anthropic format
                content = chunk.delta.text if chunk.delta.text else ""
            else:
                # Try to extract content from other formats or use empty string
                content = getattr(chunk, 'content', '')
            
            # Append to the full content
            full_content += content if content else ""
            
            # Prepare the SSE event data using the Pydantic model
            response = ChatStreamResponse(
                content=content if content else "",
                done=False
            )
            
            # Yield the SSE formatted event
            yield f"data: {json.dumps(response.model_dump())}\n\n"
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)
        
        # Send a final event indicating completion
        response = ChatStreamResponse(
            content="",
            done=True,
            conversation_id=conversation_id
        )
        yield f"data: {json.dumps(response.model_dump())}\n\n"
        
        # Save the assistant's response to the database
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
            model=model
        )
        
    except Exception as e:
        # Send an error event
        error_response = ChatStreamResponse(
            error=str(e),
            done=True,
            conversation_id=conversation_id
        )
        yield f"data: {json.dumps(error_response.model_dump())}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Chat endpoint that streams responses from the LLM.
    
    If conversation_session_id is not provided, creates a new conversation.
    Otherwise, appends to the existing conversation.
    
    Args:
        request: The chat request containing model, message, and optional conversation_session_id
        
    Returns:
        A streaming response with the chat completion
    """
    model = request.model
    user_message = request.message
    conversation_id = request.conversation_session_id
    system_prompt = request.system_prompt
    summarize_history = request.summarize_history
    
    # Check if the model is available
    available_models = llm_service.get_available_models()
    model_found = False
    
    for provider in available_models:
        if model in available_models[provider]:
            model_found = True
            break
    
    if not model_found:
        raise HTTPException(status_code=400, detail=f"Model '{model}' is not available")
    
    # If no conversation_id is provided, create a new conversation
    if not conversation_id:
        # Create a title from the first user message (truncated if too long)
        title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        
        # Create a new conversation
        conversation_id = create_conversation(
            title=title,
            model=model,
            system_prompt=system_prompt
        )
    
    # Add the user message to the conversation
    add_message(
        conversation_id=conversation_id,
        role="user",
        content=user_message
    )
    
    # Get the conversation history
    messages = llm_service.get_message_history(
        conversation_id=conversation_id,
        summarize=summarize_history
    )
    
    # Create the streaming response
    return StreamingResponse(
        stream_generator(model, messages, conversation_id),
        media_type="text/event-stream"
    )
