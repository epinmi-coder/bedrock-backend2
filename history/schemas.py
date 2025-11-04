# History schemas
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

class ConversationCreate(BaseModel):
    user_id: str
    chat_id: Optional[str] = None
    user_input: str
    bedrock_response: str
    chat_metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    chat_id: str
    message_uid: str
    response_session_id: Optional[str] = None
    user_input: str
    response: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationList(BaseModel):
    items: List[ConversationResponse]
    total: int
    offset: int
    limit: int
    has_more: bool


class DeleteResponse(BaseModel):
    success: bool
    message: str
