import asyncio
import enum
import json
from typing import Optional

import aioconsole
from reactivestreams.subscriber import DefaultSubscriber
from reactivestreams.subscription import DefaultSubscription
from rsocket.extensions.helpers import composite, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.helpers import single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from app.logs import logger
from app.schemas import LoginRequest, AuthResponse, User, RegisterRequest, RegisterResponse, LogoutRequest, \
    LogoutResponse, FindUsersRequest, FindUsersResponse, CheckSessionResponse, GetUserByIdRequest, \
    GetUserByIdResponse, Message, SendMessageRequest, SendMessageResponse, OnlineMetric
from app.utils import schema_to_bytes, payload_to_schema


class ChatClient:
    def __init__(self, rsocket: RSocketClient):
        self._rsocket = rsocket

        self._message_subscriber: Optional = None

        self._session: str = None
        self._user: User = None
        self._current_user_dialog: User = None
        self._online = False
        self._online_sending_task = None

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
            self._online_sending_task = asyncio.create_task(self.send_online())
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
        self.stop_sending_online()
        print(f'successfully logged out')
        self._session = None
        self._user = None
        self._current_user_dialog = None

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
        self.listen_for_messages()
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
            self.stop_listening_for_messages()

    async def get_dialog_messages(self):
        pass

    async def send_message(self, message_text: str):
        request = SendMessageRequest(from_user_id=self._user.id,
                                     to_user_id=self._current_user_dialog.id,
                                     message_text=message_text,
                                     session=self._session)
        request_payload = Payload(schema_to_bytes(request), composite(route('send_message')))
        response_payload = await self._rsocket.request_response(request_payload)
        response: SendMessageResponse = payload_to_schema(response_payload, SendMessageResponse)
        if response.success:
            pass
        else:
            response: CheckSessionResponse = payload_to_schema(response_payload, CheckSessionResponse)
            print(f'error: {response.error}; you must logged in for perform this operation')

    async def send_online(self):
        self._online = True
        # logger.debug('start sending online')
        while self._online:
            await asyncio.sleep(5)
            payload = Payload(schema_to_bytes(OnlineMetric(session=self._session)),
                              metadata=composite(route('online')))
            await self._rsocket.fire_and_forget(payload)
            # logger.debug('send online')

    def stop_sending_online(self):
        self._online = False
        # logger.debug('stop sending online')

    def listen_for_messages(self):
        def print_message(data: bytes):
            message = Message.model_validate(json.loads(data))
            if message.from_user.id == self._current_user_dialog.id:
                print(f'message from {message.from_user}: {message.message_text}')

        class MessageListener(DefaultSubscriber, DefaultSubscription):
            def __init__(self):
                super(MessageListener, self).__init__()

            def on_next(self, value, is_complete=False):
                print_message(value.data)

            def on_error(self, exception: Exception):
                print(exception)

            def cancel(self):
                self.subscription.cancel()

        self._message_subscriber = MessageListener()
        self._rsocket.request_stream(
            Payload(metadata=composite(route('messages.incoming')))
        ).subscribe(self._message_subscriber)

    def stop_listening_for_messages(self):
        self._message_subscriber.cancel()


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
            cmd = await aioconsole.ainput('cmd: ')
            if cmd in CommandsEnum.LOGIN.value:
                username = await aioconsole.ainput('username: ')
                await user.login(username)
            elif cmd in CommandsEnum.REGISTER.value:
                username = await aioconsole.ainput('username: ')
                await user.register(username)
            elif cmd in CommandsEnum.LOGOUT.value:
                await user.logout()
            elif cmd in CommandsEnum.FIND_USERS.value:
                username_part = await aioconsole.ainput('username_part: ')
                await user.find_users(username_part)
            elif cmd in CommandsEnum.SET_DIALOG.value:
                with_user_id = await aioconsole.ainput('with_user_id: ')
                try:
                    with_user_id = int(with_user_id)
                except ValueError:
                    print('with_user_id must be int')
                else:
                    dialog_user = await user.set_dialog(with_user_id)
                    if dialog_user:
                        print(f'start messaging with user {dialog_user}')
                        while True:
                            message_text = await aioconsole.ainput(f'message to {dialog_user}: ')
                            if message_text in CommandsEnum.QUIT_DIALOG.value:
                                break
                            await user.send_message(message_text)


if __name__ == "__main__":
    asyncio.run(main())
