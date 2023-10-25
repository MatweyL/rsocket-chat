import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str


class Message(BaseModel):
    id: int
    message_text: str
    from_user_id: int
    to_user_id: int
    from_user: User
    to_user: User
    load_timestamp: Optional[datetime.datetime] = None


class BaseResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None


class RegisterResponse(BaseResponse):
    user: Optional[User] = None


class AuthResponse(BaseResponse):
    user: Optional[User] = None
