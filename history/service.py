# History service implementation
from typing import List, Dict, Any, Optional
import logging
import sqlalchemy as sa
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
from db.models import Chats
import uuid
from logger import setup_logger

# Setup module logger with file and console handlers
logger = setup_logger(__name__)


class ChatHistoryService:
    """Service layer for chat-history related operations using asynchronous database operations."""

    async def persist(
        self,
        user_id: str,
        chat_id: str,
        user_input: str,
        bedrock_response: str,
        chat_metadata: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Persist a conversation to the database"""
        try:
            new_chat = Chats(
                id=uuid.uuid4(),
                user_id=user_id,
                chat_id=uuid.UUID(chat_id) if chat_id else uuid.uuid4(),
                user_input=user_input,
                bedrock_response=bedrock_response,
                chat_metadata=chat_metadata or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            if session:
                session.add(new_chat)
                await session.commit()
                await session.refresh(new_chat)
            
            return {
                "id": str(new_chat.id),
                "chat_id": str(new_chat.chat_id),
                "user_id": new_chat.user_id,
                "created_at": new_chat.created_at.isoformat()
            }
        
        except Exception as e:
            if session:
                await session.rollback()
            logger.exception(f"Failed to persist conversation: {e}")
            raise
        
        

    async def fetch(
        self,
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch conversation history for a user, ordered by most recent first."""
        statement = (
            select(Chats)
            .where(Chats.user_id == user_id)
            .order_by(Chats.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        conversations = results.all()
        
        # Convert SQLModel objects to dictionaries
        return [
            {
                "id": str(conv.id),
                "user_id": conv.user_id,
                "chat_id": str(conv.chat_id),
                "user_input": conv.user_input,
                "bedrock_response": conv.bedrock_response,
                "chat_metadata": conv.chat_metadata,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            }
            for conv in conversations
        ]

    async def fetch_by_chat(
        self,
        session: AsyncSession,
        chat_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch all messages in a specific chat conversation."""
        statement = (
            select(Chats)
            .where(Chats.chat_id == chat_id)
            .order_by(Chats.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        conversations = results.all()
        
        # Convert SQLModel objects to dictionaries
        return [
            {
                "id": str(conv.id),
                "user_id": conv.user_id,
                "chat_id": str(conv.chat_id),
                "user_input": conv.user_input,
                "bedrock_response": conv.bedrock_response,
                "chat_metadata": conv.chat_metadata,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            }
            for conv in conversations
        ]

    async def get_conversation_count(
        self,
        session: AsyncSession,
        user_id: str,
        chat_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Get total count of conversations for pagination."""
        try:
            if chat_id:
                statement = select(sa.func.count()).select_from(Chats).where(
                    Chats.chat_id == chat_id
                )
            else:
                statement = select(sa.func.count()).select_from(Chats).where(
                    Chats.user_id == user_id
                )
            
            result = await session.execute(statement)
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting conversation count: {e}")
            return 0

    async def delete_chat_session(
        self,
        session: AsyncSession,
        chat_id: uuid.UUID,
        user_id: str = "anonymous"
    ) -> bool:
        """Delete all conversations in a chat session"""
        try:
            statement = select(Chats).where(Chats.chat_id == chat_id)
            result = await session.exec(statement)
            conversations = result.all()
            
            if not conversations:
                logger.warning(f"Chat session {chat_id} not found")
                return False
            
            for conv in conversations:
                await session.delete(conv)
            
            await session.commit()
            logger.info(f"Deleted {len(conversations)} conversations from chat session {chat_id}")
            return True
        except Exception as e:
            await session.rollback()
            logger.exception(f"Failed to delete chat session: {e}")
            return False
            statement = select(Chats).where(
                Chats.chat_id == chat_id,
                Chats.user_id == user_id
            )
            result = await session.exec(statement)
            conversations = result.all()
            
            await session.commit()
            logger.info(f"Renamed conversations in chat {chat_id} to '{new_title}'")
            return new_title
            
        except Exception as e:
            await session.rollback()
            logger.exception(f"Failed to rename chat: {e}")
            return 0
