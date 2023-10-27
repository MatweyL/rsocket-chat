import asyncio

from rsocket.extensions.helpers import composite, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import utf8_decode, single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from app.logs import logger
from app.schemas import LoginRequest, AuthResponse, User, RegisterRequest, RegisterResponse
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


async def main():
    connection = await asyncio.open_connection('localhost', 1875)
    async with RSocketClient(single_transport_provider(TransportTCP(*connection)),
                             metadata_encoding=WellKnownMimeTypes.MESSAGE_RSOCKET_COMPOSITE_METADATA) as client:
        user = ChatClient(client)
        cmd = ''
        print("""commands:
         - login: enter username
         - register: enter username
         """)
        while cmd != 'exit':
            cmd = input('cmd: ')
            if cmd == 'login':
                username = input('username: ')
                await user.login(username)
            elif cmd == 'register':
                username = input('username: ')
                await user.register(username)


if __name__ == "__main__":
    asyncio.run(main())
