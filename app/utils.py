from uuid import uuid4

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
