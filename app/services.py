from asyncio import Queue
from typing import Dict, List

from app import schemas
from app.cruds import UserAccountCRUD, MessageCRUD
from app.schemas import RegisterResponse, AuthResponse, Dialog, Message, User, CheckSessionResponse, LoginRequest, \
    RegisterRequest, BaseRequest, FindUsersRequest, GetDialogsRequest, SendMessageRequest, GetDialogMessagesRequest


class AuthMiddleWare:

    def __init__(self, active_users: Dict[str, schemas.User]):
        self._active_users: Dict[str, schemas.User] = active_users

    def check_session(self, request: BaseRequest) -> CheckSessionResponse:
        session = request.session
        if session in self._active_users:
            return CheckSessionResponse(success=True, session=session)
        return CheckSessionResponse(success=False, session=session)


class AuthService:

    def __init__(self, user_account_crud: UserAccountCRUD,
                 active_users: Dict[str, schemas.User]):
        self._user_account_crud = user_account_crud
        self._active_users: Dict[str, schemas.User] = active_users

    def register(self, request: RegisterRequest) -> RegisterResponse:
        try:
            user = self._user_account_crud.create(request.username)
        except BaseException as e:
            response = RegisterResponse(success=False, error=str(e))
        else:
            response = RegisterResponse(user=user)
        return response

    def auth(self, request: LoginRequest) -> AuthResponse:
        username = request.username
        try:
            user = self._user_account_crud.get_by_username(username)
        except BaseException as e:
            response = AuthResponse(success=False, error=str(e))
        else:
            session = username + '_session'
            self._active_users[session] = user
            response = AuthResponse(user=user, session=session)
        return response


class ChatService:

    def __init__(self, user_account_crud: UserAccountCRUD, message_crud: MessageCRUD, finding_limit: int = 10):
        self._user_account_crud = user_account_crud
        self._message_crud = message_crud
        self._finding_limit = finding_limit

    def find_users(self, request: FindUsersRequest) -> List[User]:
        username_part = request.username_part
        found_users = self._user_account_crud.find_by_username_part(username_part, self._finding_limit)
        return found_users

    def get_dialog_messages(self, request: GetDialogMessagesRequest) -> List[Message]:
        user_id = request.user_id
        with_user_id = request.with_user_id
        dialog_messages = self._message_crud.get_user_dialog(user_id, with_user_id)
        return dialog_messages

    def get_dialogs(self, request: GetDialogsRequest) -> List[Dialog]:
        user_id = request.user_id
        user = self._user_account_crud.get_by_id(user_id)
        dialogs_users_ids = self._message_crud.get_user_dialogs_users_ids(user_id)
        dialogs_users = [self._user_account_crud.get_by_id(dialog_user_id) for dialog_user_id in dialogs_users_ids]
        return [Dialog(user=user, with_user=dialog_user) for dialog_user in dialogs_users]

    def send_message(self, request: SendMessageRequest) -> Message:
        message_text: str = request.message_text
        from_user_id: int = request.from_user_id
        to_user_id: int = request.to_user_id
        message = self._message_crud.create(message_text, from_user_id, to_user_id)
        return message


class NewMessagesStorage:

    def __init__(self):
        self._new_messages: Dict[Dialog, Queue] = {}

    def add(self, dialog: Dialog, message: Message):
        pass

    def get_new_messages_count(self, dialog: Dialog) -> int:
        try:
            new_messages_count = len(self._new_messages[dialog])
        except KeyError:
            new_messages_count = 0
        return new_messages_count

    def get_new_messages(self, dialog: Dialog) -> List[Message]:
        pass
