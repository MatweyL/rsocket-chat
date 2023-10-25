from asyncio import Queue
from typing import Dict, List

from app.cruds import UserAccountCRUD, MessageCRUD
from app.schemas import RegisterResponse, AuthResponse, Dialog, Message, User


class AuthService:

    def __init__(self, user_account_crud: UserAccountCRUD):
        self._user_account_crud = user_account_crud

    def register(self, username: str) -> RegisterResponse:
        try:
            user = self._user_account_crud.create(username)
        except BaseException as e:
            response = RegisterResponse(success=False, error=str(e))
        else:
            response = RegisterResponse(user=user)
        return response

    def auth(self, username: str) -> AuthResponse:
        try:
            user = self._user_account_crud.get_by_username(username)
        except BaseException as e:
            response = AuthResponse(success=False, error=str(e))
        else:
            response = AuthResponse(user=user)
        return response


class ChatService:

    def __init__(self, user_account_crud: UserAccountCRUD, message_crud: MessageCRUD, finding_limit: int = 10):
        self._user_account_crud = user_account_crud
        self._message_crud = message_crud
        self._finding_limit = finding_limit

    def find_users(self, username_part: str) -> List[User]:
        found_users = self._user_account_crud.find_by_username_part(username_part, self._finding_limit)
        return found_users

    def get_dialog_messages(self, user_id: int, with_user_id: int) -> List[Message]:
        dialog_messages = self._message_crud.get_user_dialog(user_id, with_user_id)
        return dialog_messages

    def get_dialogs(self, user_id: int) -> List[Dialog]:
        user = self._user_account_crud.get_by_id(user_id)
        dialogs_users_ids = self._message_crud.get_user_dialogs_users_ids(user_id)
        dialogs_users = [self._user_account_crud.get_by_id(dialog_user_id) for dialog_user_id in dialogs_users_ids]
        return [Dialog(user=user, with_user=dialog_user) for dialog_user in dialogs_users]

    def send_message(self, message_text: str, from_user_id: int, to_user_id: int) -> Message:
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
