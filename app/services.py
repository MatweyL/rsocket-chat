from app.cruds import UserAccountCRUD, MessageCRUD
from app.schemas import RegisterResponse, AuthResponse


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

    def __init__(self, user_account_crud: UserAccountCRUD, message_crud: MessageCRUD):
        self._user_account_crud = user_account_crud
        self._message_crud = message_crud

    def find_users(self, username_part: str):
        pass

    def get_dialog(self, user_id: int, with_user_id: int):
        pass

    def get_dialogs(self, user_id: int):
        pass

    def send_message(self, message_text: str, from_user_id: int, to_user_id: int):
        pass

