import asyncio
import json
import logging
import uuid
from asyncio import Queue
from dataclasses import dataclass, field
from typing import Dict, Optional
from weakref import WeakValueDictionary

from reactivestreams.publisher import DefaultPublisher
from reactivestreams.subscriber import Subscriber
from reactivestreams.subscription import DefaultSubscription
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import utf8_decode, create_response
from rsocket.local_typing import Awaitable
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP

from shared import Message, encode_dataclass


class SessionId(str):
    pass


@dataclass()
class UserSessionData:
    username: str
    session_id: SessionId
    messages: Queue = field(default_factory=Queue)


@dataclass(frozen=True)
class ChatData:
    user_session_by_id: Dict[SessionId, UserSessionData] = field(default_factory=WeakValueDictionary)


chat_data = ChatData()


def find_session_by_username(username: str) -> Optional[UserSessionData]:
    try:
        return next(session for session in chat_data.user_session_by_id.values() if
                    session.username == username)
    except StopIteration:
        return None


class ChatUserSession:

    def __init__(self):
        self._session: Optional[UserSessionData] = None

    def router_factory(self):
        router = RequestRouter()

        @router.response('login')
        async def login(payload: Payload) -> Awaitable[Payload]:
            username = utf8_decode(payload.data)

            logging.info(f'New user: {username}')

            session_id = SessionId(uuid.uuid4())
            self._session = UserSessionData(username, session_id)
            chat_data.user_session_by_id[session_id] = self._session

            return create_response(ensure_bytes(session_id))

        @router.response('message')
        async def send_message(payload: Payload) -> Awaitable[Payload]:
            message = Message(**json.loads(payload.data))

            logging.info('Received message for user: %s', message.user)

            target_message = Message(self._session.username, message.content)

            session = find_session_by_username(message.user)
            await session.messages.put(target_message)

            return create_response()

        @router.stream('messages.incoming')
        async def messages_incoming():
            class MessagePublisher(DefaultPublisher, DefaultSubscription):
                def __init__(self, session: UserSessionData):
                    self._session = session
                    self._sender = None

                def cancel(self):
                    self._sender.cancel()

                def subscribe(self, subscriber: Subscriber):
                    super(MessagePublisher, self).subscribe(subscriber)
                    subscriber.on_subscribe(self)
                    self._sender = asyncio.create_task(self._message_sender())

                async def _message_sender(self):
                    while True:
                        next_message = await self._session.messages.get()
                        next_payload = Payload(encode_dataclass(next_message))
                        self._subscriber.on_next(next_payload)

            return MessagePublisher(self._session)

        return router


class CustomRoutingRequestHandler(RoutingRequestHandler):
    def __init__(self, session: ChatUserSession):
        super().__init__(session.router_factory())
        self._session = session


def handler_factory():
    return CustomRoutingRequestHandler(ChatUserSession())


async def run_server():
    def session(*connection):
        RSocketServer(TransportTCP(*connection), handler_factory=handler_factory)

    async with await asyncio.start_server(session, 'localhost', 6565) as server:
        await server.serve_forever()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())
