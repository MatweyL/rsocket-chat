from typing import Type
from uuid import uuid4

from pydantic import BaseModel
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import utf8_decode
from rsocket.payload import Payload

from app import schemas
from app.models import Message, User


def get_uid():
    return str(uuid4())


def message_model_as_schema(message: Message) -> schemas.Message:
    message_dict = message.__dict__
    message_dict['from_user'] = message.from_user.__dict__
    message_dict['to_user'] = message.to_user.__dict__
    return schemas.Message.model_validate(message_dict)


def user_model_as_schema(user: User) -> schemas.User:
    return schemas.User.model_validate(user.__dict__)


def payload_to_schema(payload: Payload, schema_class: Type[BaseModel]) -> BaseModel:
    raw_request: dict = utf8_decode(payload.data)
    return schema_class.model_validate_json(raw_request)


def schema_to_bytes(schema: BaseModel) -> bytes:
    return ensure_bytes(schema.model_dump_json())
