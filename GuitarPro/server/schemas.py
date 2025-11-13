from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from database.models import MessageRole


class MessageResponse(BaseModel):
    detail: str


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class RegisterResponse(BaseModel):
    message: str
    user: UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ChatCreate(BaseModel):
    title: Optional[str] = None


class ChatUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class ChatRead(BaseModel):
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1)


class MessageRead(BaseModel):
    id: int
    role: MessageRole
    content: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


ChatList = List[ChatRead]
MessageList = List[MessageRead]
