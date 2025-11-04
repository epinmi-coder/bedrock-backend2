# Chat service implementation
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from bedrock_agent import bedrock_agent
from db.models import Chats
from logger import setup_logger
from history.service import ChatHistoryService 

# Setup module logger with file and console handlers
logger = setup_logger(__name__)

history_service = ChatHistoryService()

class ChatService:
    def __init__(self):
        self.rate_limit = 10  # requests per minute
        self.rate_limit_window = 60  # seconds

    async def _check_rate_limit(self, user_id: str, session: AsyncSession) -> bool:
        """Check if user has exceeded rate limit"""
        if not user_id or user_id == "anonymous":
            # No rate limit for anonymous users (or apply a different limit)
            return True

        try:
            # Get recent requests in window
            from datetime import timedelta
            window_start = datetime.now(timezone.utc) - timedelta(seconds=self.rate_limit_window)
            
            statement = select(Chats).where(
                Chats.user_id == user_id,  # Fixed: was session_id, should be user_id
                Chats.created_at >= window_start
            )
            result = await session.exec(statement)
            recent_requests = len(result.scalars().all())
            
            logger.debug(f"Rate limit check for {user_id}: {recent_requests}/{self.rate_limit} requests")
            return recent_requests < self.rate_limit
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            # Allow request if rate limit check fails
            return True

    async def process_chat_request(
        self,
        session: AsyncSession,
        user_query: str,
        chat_id: Optional[str] = None,
        user_id: str = "anonymous",
        message_uid: Optional[str] = None
    ) -> Dict[str, Any]:
        
        logger.info(f"🤖 Processing chat request")
        logger.debug(f"Query length: {len(user_query)} chars")
        logger.debug(f"chat_id: {chat_id}, message_uid: {message_uid}")
        
        try:

            logger.debug("✅ Rate limit check passed")

            # Generate required IDs for table structure
            chat_id = chat_id or str(uuid.uuid4())
            message_uid = message_uid or str(uuid.uuid4())
            response_session_id = str(uuid.uuid4())  # Backend generates this
            
            logger.debug(f"Generated IDs - chat_id: {chat_id}, message_uid: {message_uid}, response_session_id: {response_session_id}")
            # Process request with Bedrock
            logger.info("🔄 Processing request with Bedrock...")
            
            # Call Bedrock service - returns question and response
            result = bedrock_agent.process_request(user_query)
            
            logger.info("✅ Bedrock processing completed")
            logger.debug(f"Bedrock result: question={result.get('question', '')[:50]}..., success={result.get('success')}")

            if result and result.get("success"):
                # Process the question and response returned by Bedrock
                question = result.get("question", user_query)
                bedrock_response = result.get("response", "")
                
                response = {
                    "response": bedrock_response,
                    "chat_id": chat_id,
                    "message_uid": message_uid,
                    "response_session_id": response_session_id,
                    "metadata": {
                        "question": question,
                        "bedrock_processed": True,
                        "chat_id": chat_id,
                        "message_uid": message_uid,
                        "response_session_id": response_session_id,
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "status": "success"
                }

                # Persist conversation to database
                try:
                    # Use the question and response from Bedrock processing
                    persisted = await history_service.persist(
                        user_id=user_id,
                        chat_id=chat_id,
                        user_input=question,  
                        bedrock_response=bedrock_response,
                        chat_metadata=response.get("metadata", {}),
                        session=session
                    )

                    response["response_id"] = persisted.get("id")
                    logger.info(f"✅ Conversation persisted with ID: {persisted.get('id')}")
                except Exception as e:
                    logger.exception(f"Failed to persist conversation: {e}; continuing to return response")
                
                return response

            # Handle case where Bedrock processing failed
            logger.warning("⚠️ Bedrock processing failed or returned invalid response")
            return {
                "error": "Failed to process the query completely",
                "response": result.get("response", "I'm sorry, I couldn't process your request."),
                "chat_id": chat_id,
                "message_uid": message_uid,
                "metadata": {
                    "question": result.get("question", user_query),
                    "bedrock_error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "status": "partial_failure"
            }

        except Exception as e:
            logger.error(f"Chat service error: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "response": "I'm sorry, an error occurred while processing your request.",
                "status": "error",
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error_type": type(e).__name__
                }
            }

