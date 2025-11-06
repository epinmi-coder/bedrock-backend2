# Chat schemas - Aligned with frontend and database
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID


class ChatRequest(BaseModel):
    """Request schema for sending a message"""
    user_input: str = Field(..., min_length=1, max_length=4000, alias="message")
    chat_id: Optional[str] = None  
    message_uid: Optional[str] = None
    
    class Config:
        populate_by_name = True  # Allows both "user_input" and "message"


class ChatMetadata(BaseModel):
    """Metadata included in chat responses"""
    prompt_token_count: Optional[int] = Field(default=0, alias="tokens_used")
    total_token_count: Optional[int] = 0
    tools_called: Optional[list] = Field(default_factory=list)
    bedrock_processed: bool = False
    model_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    class Config:
        populate_by_name = True


class ChatResponse(BaseModel):
    """Response schema for chat messages - matches frontend expectations"""
    response: str  # Bot's reply text
    chat_id: Optional[str] = None
    message_uid: Optional[str] = None
    response_session_id: Optional[str] = None
    response_id: Optional[str] = None  # Database record ID
    metadata: Optional[ChatMetadata] = None
    status: str = Field(default="success")
    error: Optional[str] = None
