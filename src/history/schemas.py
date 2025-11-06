# History schemas - Matches database model and frontend expectations
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class ConversationItem(BaseModel):
    """Single conversation item returned by history endpoints"""
    id: str
    user_id: str
    chat_id: str
    message_uid: Optional[str] = None
    response_session_id: Optional[str] = None
    user_input: str
    response: str  # Matches frontend expectation and new DB field
    chat_metadata: Optional[Dict[str, Any]] = None  # Matches DB field name
    created_at: str
    updated_at: str
    
    class Config:
        # Allow both response and bedrock_response for backward compatibility
        populate_by_name = True


class ConversationList(BaseModel):
    """Response for history list endpoints"""
    items: List[ConversationItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class DeleteResponse(BaseModel):
    """Response for delete operations"""
    success: bool
    message: str
    chat_id: Optional[str] = None
