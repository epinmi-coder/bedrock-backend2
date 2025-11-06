# Chat routes
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any, Optional
from .schemas import ChatRequest, ChatResponse
from .service import ChatService
from src.db.main import get_session
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
chat_router = APIRouter()

# Initialize chat service
chat_service = ChatService()

@chat_router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session)
):   
    """Send a message and get AI response from Bedrock"""
    # Process the chat request with hierarchical ID structure
    response = await chat_service.process_chat_request(
        user_query=request.user_input,
        session=session,
        chat_id=request.chat_id,
        message_uid=request.message_uid
    )
    
    # Check if response indicates an error
    if response.get("status") == "error":
        raise HTTPException(
            status_code=429 if "rate limit" in response.get("error", "").lower() else 500,
            detail=response.get("error", "Internal server error")
        )
    
    return response
    

@chat_router.get("/health")
async def chat_health_check():
    """Health check for chat service (public endpoint)"""
    try:
        # Check if Bedrock service is available
        bedrock_status = "available" if chat_service else "unavailable"
        
        return {
            "status": "healthy",
            "service": "chat",
            "bedrock_service": bedrock_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
