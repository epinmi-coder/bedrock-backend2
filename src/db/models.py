# Database models for chat history
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column


class Chats(SQLModel, table=True):
    __tablename__ = "chats"
    __table_args__ = {'extend_existing': True}
    
    id: uuid.UUID = Field(
        sa_column=Column(pg.UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    )
    chat_id: uuid.UUID = Field(sa_column=Column(pg.UUID, nullable=False, index=True))
    user_id: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False, index=True))
    message_uid: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID, nullable=True, index=True))
    response_session_id: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID, nullable=True))
    user_input: str
    response: Optional[str] = None  # Changed from bedrock_response to response
    chat_metadata: Optional[dict] = Field(sa_column=Column(pg.JSONB), default=None)
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, nullable=False, index=True)
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now, nullable=False)
    )
    def __repr__(self):
        return f"<Chat {self.chat_id}>"



class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(
        sa_column=Column(pg.VARCHAR, nullable=False, server_default="user")
    )
    is_verified: bool = Field(default=False)
    password_hash: str = Field(
        sa_column=Column(pg.VARCHAR, nullable=False), exclude=True
    )
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<User {self.username}>"