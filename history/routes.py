# History routes
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from db.main import get_session
from auth.dependencies import get_current_user, get_current_user_optional
from history.service import ChatHistoryService

logger = logging.getLogger(__name__)
history_router = APIRouter()

history_service = ChatHistoryService()

@history_router.get("/")
async def get_my_chat_history(
    chat_id: Optional[str] = Query(None),
    user_id: str = Query("anonymous"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get chat history for a user or specific chat"""
    try:
        if chat_id:
            # Get specific chat history
            items = await history_service.fetch_by_chat(
                session=session,
                chat_id=UUID(chat_id),
                limit=limit,
                offset=offset
            )
            total = await history_service.get_conversation_count(
                session=session,
                user_id=user_id,
                chat_id=UUID(chat_id)
            )
        else:
            # Get all user history
            items = await history_service.fetch(
                session=session,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            total = await history_service.get_conversation_count(
                session=session,
                user_id=user_id
            )
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        }
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@history_router.get("/conversations")
async def get_conversations(
    user_id: str = Query("anonymous"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get all conversations for a user"""
    try:
        items = await history_service.fetch(
            session=session,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        total = await history_service.get_conversation_count(
            session=session,
            user_id=user_id
        )
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        }
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@history_router.get("/conversations/{chat_id}")
async def get_chat_conversations(
    chat_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get all messages in a specific chat conversation"""
    try:
        items = await history_service.fetch_by_chat(
            session=session,
            chat_id=UUID(chat_id),
            limit=limit,
            offset=offset
        )
        
        total = await history_service.get_conversation_count(
            session=session,
            user_id="anonymous",  # Will be replaced with actual user when auth is enabled
            chat_id=UUID(chat_id)
        )
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        }
    except Exception as e:
        logger.error(f"Error fetching chat conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@history_router.delete("/conversations/{chat_id}")
async def delete_chat(
    chat_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete all conversations in a chat session"""
    try:
        deleted = await history_service.delete_chat_session(
            session=session,
            chat_id=UUID(chat_id)
        )
        
        if deleted:
            return {
                "success": True,
                "message": "Chat session deleted successfully",
                "chat_id": chat_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



