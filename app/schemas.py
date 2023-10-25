import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id and isinstance(other, User)


class Message(BaseModel):
    id: int
    message_text: str
    from_user_id: int
    to_user_id: int
    from_user: User
    to_user: User
    load_timestamp: Optional[datetime.datetime] = None


class Dialog(BaseModel):
    user: User
    with_user: User

    def __hash__(self):
        return hash(self.user.id) + hash(self.with_user.id)

    def __eq__(self, other):
        return self.user.id == other.user.id and self.with_user.id == other.with_user.id


class BaseResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None


class RegisterResponse(BaseResponse):
    user: Optional[User] = None


class AuthResponse(BaseResponse):
    user: Optional[User] = None
