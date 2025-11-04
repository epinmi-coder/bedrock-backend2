# Chat schemas
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

class ChatRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=4000, alias="message")
    chat_id: Optional[str] = None  
    message_uid: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ChatMetadata(BaseModel):
    question: Optional[str] = None
    bedrock_processed: bool = False
    chat_id: Optional[str] = None
    message_uid: Optional[str] = None
    response_session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[str] = None
    tokens_used: int = 0
    model_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    chat_id: Optional[str] = None
    message_uid: Optional[str] = None
    response_session_id: Optional[str] = None
    metadata: Optional[ChatMetadata] = None
    status: str = Field(default="success")
    error: Optional[str] = None
    response_id: Optional[str] = None


class ChatHistoryEntry(BaseModel):
    user_input: str
    response: str
    timestamp: datetime
    session_id: Optional[UUID] = None


class ChatHistoryResponse(BaseModel):
    history: List[ChatHistoryEntry]
    count: int
    has_more: bool = False
