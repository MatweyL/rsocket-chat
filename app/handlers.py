import asyncio
import datetime
from typing import Awaitable, Type, Dict

from pydantic import BaseModel
from reactivestreams.publisher import DefaultPublisher
from reactivestreams.subscriber import Subscriber, DefaultSubscriber
from reactivestreams.subscription import DefaultSubscription
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import create_response, utf8_decode
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler

from app import schemas
from app.cruds import MessageCRUD, UserAccountCRUD
from app.database import create_session
from app.logs import logger
from app.schemas import LoginRequest, RegisterRequest, LogoutRequest, FindUsersRequest, GetUserByIdRequest, \
    SendMessageRequest, User, Message, OnlineMetric, MetricRequest, TotalOnlineMetric
from app.services import AuthService, ChatService, AuthMiddleWare
from app.utils import payload_to_schema, schema_to_bytes

session = create_session('chat.db')
user_account_crud = UserAccountCRUD(session)
message_crud = MessageCRUD(session)
logged_in_users: Dict[str, schemas.User] = {}
online_sessions: Dict[str, float] = {}
auth_service = AuthService(user_account_crud, logged_in_users)
chat_service = ChatService(user_account_crud, message_crud)
auth_middleware = AuthMiddleWare(logged_in_users)

incoming_messages: asyncio.Queue = asyncio.Queue()
SESSION_INACTIVE_PERIOD_S = 10


async def check_online_sessions():
    while True:
        await asyncio.sleep(10)
        offline_sessions = []
        for user_session, timestamp in online_sessions.items():
            if datetime.datetime.now().timestamp() - timestamp > SESSION_INACTIVE_PERIOD_S:
                offline_sessions.append(user_session)
        for offline_session in offline_sessions:
            if offline_session in online_sessions:
                online_sessions.pop(offline_session)
            if offline_session in logged_in_users:
                print(f'logged out {logged_in_users[offline_session]}')
                logged_in_users.pop(offline_session)


def handler_factory() -> RoutingRequestHandler:
    router = RequestRouter()

    @router.response('login')
    async def login(payload: Payload) -> Awaitable[Payload]:
        request: LoginRequest = payload_to_schema(payload, LoginRequest)
        response = auth_service.auth(request)
        if response.success:
            logged_in_users[response.session] = response.user
            online_sessions[response.session] = datetime.datetime.now().timestamp()
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
        if response.success:
            online_sessions.pop(request.session)
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
        incoming_messages.put_nowait(response.message)
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

    @router.fire_and_forget('online')
    async def receive_online(payload: Payload):
        metric = payload_to_schema(payload, OnlineMetric)
        online_sessions[metric.session] = datetime.datetime.now().timestamp()

    @router.channel('statistics')
    async def send_statistics(payload: Payload):

        request: MetricRequest = payload_to_schema(payload, MetricRequest)

        class StatisticsChannel(DefaultPublisher, DefaultSubscriber, DefaultSubscription):

            def __init__(self, requested_statistics: MetricRequest):
                super().__init__()
                self._requested_statistics = requested_statistics

            def cancel(self):
                self._sender.cancel()

            def subscribe(self, subscriber: Subscriber):
                super().subscribe(subscriber)
                subscriber.on_subscribe(self)
                self._sender = asyncio.create_task(self._statistics_sender())

            async def _statistics_sender(self):
                while True:
                    try:
                        await asyncio.sleep(5)
                        next_message = TotalOnlineMetric(total=len(online_sessions))

                        self._subscriber.on_next(Payload(schema_to_bytes(next_message)))
                    except Exception:
                        logger.error('Statistics', exc_info=True)

            def on_next(self, value: Payload, is_complete=False):
                request = payload_to_schema(value, MetricRequest)

                logger.info(f'Received statistics request {request.ids}, {request.period_seconds}')

        response = StatisticsChannel(request)

        return response, response

    return RoutingRequestHandler(router)
