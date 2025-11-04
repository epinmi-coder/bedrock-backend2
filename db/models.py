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
    user_id: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False, index=True))
    chat_id: uuid.UUID = Field(sa_column=Column(pg.UUID, nullable=False, index=True))
    user_input: str
    bedrock_response: Optional[str] = None
    chat_metadata: Optional[dict] = Field(sa_column=Column(pg.JSONB), default=None)
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, nullable=False, index=True)
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now, nullable=False)
    )


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id: uuid.UUID = Field(
        sa_column=Column(pg.UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    )
    email: str 
    userchat_uid: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False, unique=True, index=True))
    first_name: str 
    last_name: str
    password_hash: str = Field(
        sa_column=Column(pg.VARCHAR, nullable=False), exclude=True
    )
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, nullable=False, index=True)
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now, nullable=False)
    )