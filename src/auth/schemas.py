import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class UserCreateModel(BaseModel):
    first_name: str = Field(min_length=2, max_length=25)
    last_name: str = Field(min_length=2, max_length=25)
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(max_length=100)
    password: str = Field(min_length=8) 


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime


class UserLoginModel(BaseModel):
    email: str 
    password: str 

class EmailModel(BaseModel):
    addresses: List[str]


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str
