import asyncio
import enum
from typing import Optional

from rsocket.extensions.helpers import composite, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.helpers import single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from app.schemas import LoginRequest, AuthResponse, User, RegisterRequest, RegisterResponse, LogoutRequest, \
    LogoutResponse, FindUsersRequest, FindUsersResponse, CheckSessionResponse, GetUserByIdRequest, \
    GetUserByIdResponse
from app.utils import schema_to_bytes, payload_to_schema


class ChatClient:
    def __init__(self, rsocket: RSocketClient):
        self._rsocket = rsocket

        self._session: str = None
        self._user: User = None
        self._current_user_dialog: User = None

    async def login(self, username: str):
        if self._session:
            print('cannot login from already logged in account; please, logout and try again')
            return
        request = LoginRequest(username=username)
        request_payload = Payload(schema_to_bytes(request), composite(route('login')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: AuthResponse = payload_to_schema(response_payload, AuthResponse)
        if response.success:
            print(f'successfully logged in as {response.user.username}')
            self._session = response.session
            self._user = response.user
        else:
            print('cannot login:', response.error)

    async def register(self, username: str):
        request = RegisterRequest(username=username)
        request_payload = Payload(schema_to_bytes(request), composite(route('register')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: RegisterResponse = payload_to_schema(response_payload, RegisterResponse)
        if response.success:
            print(f'successfully registered as {response.user.username}; please, auth with your credentials')
        else:
            print('cannot register:', response.error)

    async def logout(self):
        if not self._session:
            print('cannot logout: operation can be performed if you logged in')
            return
        request = LogoutRequest(session=self._session)
        request_payload = Payload(schema_to_bytes(request), composite(route('logout')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: LogoutResponse = payload_to_schema(response_payload, LogoutResponse)
        if response.success:
            print(f'successfully logged out')
            self._session = None
            self._user = None
            self._current_user_dialog = None
        else:
            print('cannot logout:', response.error)

    async def find_users(self, username_part: str):
        request = FindUsersRequest(username_part=username_part, session=self._session)
        request_payload = Payload(schema_to_bytes(request), composite(route('find_users')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: FindUsersResponse = payload_to_schema(response_payload, FindUsersResponse)
        if response.success:
            print(f'found {len(response.users)} users: ')
            for user in response.users:
                print(f'-- {user}')
        else:
            response: CheckSessionResponse = payload_to_schema(response_payload, CheckSessionResponse)
            print(f'cannot find users: {response.error}; you must logged in for perform this operation')

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        if not self._session:
            print('error: operation can be performed if you logged in')
            return
        request = GetUserByIdRequest(user_id=user_id, session=self._session)
        request_payload = Payload(schema_to_bytes(request), composite(route('get_user_by_id')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: GetUserByIdResponse = payload_to_schema(response_payload, GetUserByIdResponse)
        if response.success:
            print(f'got user: {response.user}')
            return response.user
        else:
            response: CheckSessionResponse = payload_to_schema(response_payload, CheckSessionResponse)
            print(f'cannot find users: {response.error}; you must logged in for perform this operation')

    async def get_dialogs(self):
        pass

    async def set_dialog(self, with_user_id: int) -> Optional[User]:
        if not self._session:
            print('cannot set dialog: operation can be performed if you logged in')
            return
        if with_user_id == self._user.id:
            print('you cannot messaging with yourself')
            return
        user = await self.get_user_by_id(with_user_id)
        if user is None:
            return
        if not user:
            print(f'no users with id={with_user_id}')
            return
        print(f'set current dialog with user {user}')
        self._current_user_dialog = user
        return user

    async def quit_dialog(self):
        if not self._session:
            print('cannot set dialog: operation can be performed if you logged in')
            return
        if not self._current_user_dialog:
            print('no dialog set now')
        else:
            print(f'quit from dialog: {self._current_user_dialog}')
            self._current_user_dialog = None

    async def get_dialog_messages(self):
        pass

    async def send_message(self):
        pass


class CommandsEnum(enum.Enum):
    LOGIN = ('1', 'login')
    REGISTER = ('2', 'register')
    LOGOUT = ('3', 'logout')
    FIND_USERS = ('4', 'find_users')
    SET_DIALOG = ('5', 'set_dialog')
    QUIT_DIALOG = ('6', 'quit_dialog')


async def main():
    connection = await asyncio.open_connection('localhost', 1875)
    async with RSocketClient(single_transport_provider(TransportTCP(*connection)),
                             metadata_encoding=WellKnownMimeTypes.MESSAGE_RSOCKET_COMPOSITE_METADATA) as client:
        user = ChatClient(client)
        cmd = ''
        print('commands:')
        for command in CommandsEnum:
            value = command.value
            command_text = f'\t-- {value[0]}. {value[1]}'
            print(command_text)
        while cmd != 'exit':
            cmd = input('cmd: ')
            if cmd in CommandsEnum.LOGIN.value:
                username = input('username: ')
                await user.login(username)
            elif cmd in CommandsEnum.REGISTER.value:
                username = input('username: ')
                await user.register(username)
            elif cmd in CommandsEnum.LOGOUT.value:
                await user.logout()
            elif cmd in CommandsEnum.FIND_USERS.value:
                username_part = input('username_part: ')
                await user.find_users(username_part)
            elif cmd in CommandsEnum.SET_DIALOG.value:
                with_user_id = input('with_user_id: ')
                try:
                    with_user_id = int(with_user_id)
                except ValueError:
                    print('with_user_id must be int')
                else:
                    dialog_user = await user.set_dialog(with_user_id)
                    if dialog_user:
                        print(f'start messaging with user {dialog_user}')
                        while True:
                            message_text = input(f'message to {dialog_user}: ')
                            if message_text in CommandsEnum.QUIT_DIALOG.value:
                                break


if __name__ == "__main__":
    asyncio.run(main())
