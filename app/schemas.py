import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


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
    session: Optional[str] = None


class LogoutResponse(BaseResponse):
    pass


class CheckSessionResponse(BaseResponse):
    session: Optional[str] = None


class FindUsersResponse(BaseResponse):
    users: List[User] = Field(default_factory=list)


class GetDialogMessagesResponse(BaseResponse):
    messages: List[Message] = Field(default_factory=list)


class GetDialogsResponse(BaseResponse):
    dialogs: List[Dialog] = Field(default_factory=list)


class SendMessageResponse(BaseResponse):
    message: Optional[Message] = None


class BaseRequest(BaseModel):
    session: Optional[str] = None


class LoginRequest(BaseRequest):
    username: str


class RegisterRequest(BaseRequest):
    username: str


class LogoutRequest(BaseRequest):
    pass


class FindUsersRequest(BaseRequest):
    username_part: str


class GetDialogMessagesRequest(BaseRequest):
    user_id: int
    with_user_id: int


class GetDialogsRequest(BaseRequest):
    user_id: int


class SendMessageRequest(BaseRequest):
    message_text: str
    from_user_id: int
    to_user_id: int
