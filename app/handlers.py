import asyncio
from typing import Awaitable, Type, Dict

from pydantic import BaseModel
from reactivestreams.publisher import DefaultPublisher
from reactivestreams.subscriber import Subscriber
from reactivestreams.subscription import DefaultSubscription
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import create_response, utf8_decode
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler

from app import schemas
from app.cruds import MessageCRUD, UserAccountCRUD
from app.database import create_session
from app.schemas import LoginRequest, RegisterRequest, LogoutRequest, FindUsersRequest, GetUserByIdRequest, \
    SendMessageRequest, User, Message
from app.services import AuthService, ChatService, AuthMiddleWare
from app.utils import payload_to_schema, schema_to_bytes

session = create_session('chat.db')
user_account_crud = UserAccountCRUD(session)
message_crud = MessageCRUD(session)
active_users: Dict[str, schemas.User] = {}
auth_service = AuthService(user_account_crud, active_users)
chat_service = ChatService(user_account_crud, message_crud)
auth_middleware = AuthMiddleWare(active_users)

incoming_messages: asyncio.Queue = asyncio.Queue()


def handler_factory() -> RoutingRequestHandler:
    router = RequestRouter()

    @router.response('login')
    async def login(payload: Payload) -> Awaitable[Payload]:
        request: LoginRequest = payload_to_schema(payload, LoginRequest)
        response = auth_service.auth(request)
        if response.success:
            active_users[response.session] = response.user
        return create_response(schema_to_bytes(response))

    @router.response('register')
    async def register(payload: Payload) -> Awaitable[Payload]:
        request: RegisterRequest = payload_to_schema(payload, RegisterRequest)
        response = auth_service.register(request)
        return create_response(schema_to_bytes(response))

    @router.response('logout')
    async def logout(payload: Payload) -> Awaitable[Payload]:
        request: LogoutRequest = payload_to_schema(payload, LogoutRequest)
        response = auth_service.logout(request)
        return create_response(schema_to_bytes(response))

    @router.response('find_users')
    async def find_users(payload: Payload) -> Awaitable[Payload]:
        request: FindUsersRequest = payload_to_schema(payload, FindUsersRequest)
        check_response = auth_middleware.check_session(request)
        if not check_response.success:
            return create_response(schema_to_bytes(check_response))
        response = chat_service.find_users(request)
        return create_response(schema_to_bytes(response))

    @router.response('get_user_by_id')
    async def get_user_by_id(payload: Payload) -> Awaitable[Payload]:
        request: GetUserByIdRequest = payload_to_schema(payload, GetUserByIdRequest)
        check_response = auth_middleware.check_session(request)
        if not check_response.success:
            return create_response(schema_to_bytes(check_response))
        response = chat_service.get_user_by_id(request)
        return create_response(schema_to_bytes(response))

    @router.response('send_message')
    async def send_message(payload: Payload) -> Awaitable[Payload]:
        request: SendMessageRequest = payload_to_schema(payload, SendMessageRequest)
        check_response = auth_middleware.check_session(request)
        if not check_response.success:
            return create_response(schema_to_bytes(check_response))
        response = chat_service.send_message(request)
        return create_response(schema_to_bytes(response))

    @router.stream('messages.incoming')
    async def messages_incoming():
        class MessagePublisher(DefaultPublisher, DefaultSubscription):
            def __init__(self, queue: asyncio.Queue):
                self._queue = queue
                self._sender = None

            def cancel(self):
                self._sender.cancel()

            def subscribe(self, subscriber: Subscriber):
                super(MessagePublisher, self).subscribe(subscriber)
                subscriber.on_subscribe(self)
                self._sender = asyncio.create_task(self._message_sender())

            async def _message_sender(self):
                while True:
                    message: Message = await self._queue.get()
                    message_bytes = schema_to_bytes(message)
                    next_payload = Payload(message_bytes)
                    self._subscriber.on_next(next_payload)

        return MessagePublisher(incoming_messages)

    return RoutingRequestHandler(router)
