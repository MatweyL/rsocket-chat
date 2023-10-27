import asyncio

from rsocket.extensions.helpers import composite, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import utf8_decode, single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from app.logs import logger
from app.schemas import LoginRequest, AuthResponse, User, RegisterRequest, RegisterResponse, LogoutRequest, \
    LogoutResponse, FindUsersRequest, FindUsersResponse, CheckSessionResponse
from app.utils import schema_to_bytes, payload_to_schema


class ChatClient:
    def __init__(self, rsocket: RSocketClient):
        self._rsocket = rsocket
        self._session: str = None
        self._user: User = None

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
            print(f'cannot find users: {response.error}; you must logged in for perform this operaion')

async def main():
    connection = await asyncio.open_connection('localhost', 1875)
    async with RSocketClient(single_transport_provider(TransportTCP(*connection)),
                             metadata_encoding=WellKnownMimeTypes.MESSAGE_RSOCKET_COMPOSITE_METADATA) as client:
        user = ChatClient(client)
        cmd = ''
        print("""commands:
         - 1. login: enter username
         - 2. register: enter username
         - 3. logout
         - 4. find_users: enter username part
         """)
        while cmd != 'exit':
            cmd = input('cmd: ')
            if cmd in ('login', '1'):
                username = input('username: ')
                await user.login(username)
            elif cmd in ('register', '2'):
                username = input('username: ')
                await user.register(username)
            elif cmd in ('logout', '3'):
                await user.logout()
            elif cmd in ('find_users', '4'):
                username_part = input('username_part: ')
                await user.find_users(username_part)


if __name__ == "__main__":
    asyncio.run(main())
