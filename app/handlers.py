from typing import Awaitable, Type, Dict

from pydantic import BaseModel
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import create_response, utf8_decode
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler

from app import schemas
from app.cruds import MessageCRUD, UserAccountCRUD
from app.database import create_session
from app.schemas import LoginRequest, RegisterRequest
from app.services import AuthService, ChatService, AuthMiddleWare
from app.utils import payload_to_schema, schema_to_bytes

session = create_session('chat.db')
user_account_crud = UserAccountCRUD(session)
message_crud = MessageCRUD(session)
active_users: Dict[str, schemas.User] = {}
auth_service = AuthService(user_account_crud, active_users)
chat_service = ChatService(user_account_crud, message_crud)
auth_middleware = AuthMiddleWare(active_users)


def handler_factory() -> RoutingRequestHandler:
    router = RequestRouter()

    @router.response('login')
    async def login(payload: Payload) -> Awaitable[Payload]:
        login_request: LoginRequest = payload_to_schema(payload, LoginRequest)
        auth_response = auth_service.auth(login_request)
        if auth_response.success:
            active_users[auth_response.session] = auth_response.user
        return create_response(schema_to_bytes(auth_response))

    @router.response('register')
    async def login(payload: Payload) -> Awaitable[Payload]:
        register_request: RegisterRequest = payload_to_schema(payload, RegisterRequest)
        register_response = auth_service.register(register_request)
        return create_response(schema_to_bytes(register_response))

    return RoutingRequestHandler(router)
