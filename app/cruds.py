from typing import Callable, List

from sqlalchemy.orm import Session

from app.models import User, Message
import app.schemas as schemas
from app.utils import message_model_as_schema, user_model_as_schema


class UserAccountCRUD:

    def __init__(self, session: Callable[[], Session]):
        self._session = session

    def create(self, username: str) -> schemas.User:
        with self._session() as session:
            user = session.query(User).where(User.username == username).first()
            if user:
                raise Exception("user already exists")
            user = User(username=username)
            session.add(user)
            session.commit()
            return user_model_as_schema(user)

    def get_by_username(self, username: str) -> schemas.User:
        with self._session() as session:
            user = session.query(User).where(User.username == username).first()
            if not user:
                raise Exception("user does not  exists")
            return user_model_as_schema(user)

    def get_by_id(self, user_id: int):
        with self._session() as session:
            user = session.query(User).where(User.id == user_id).first()
            if not user:
                raise Exception("user does not  exists")
            return user_model_as_schema(user)

    def find_by_username_part(self, username_part: str, limit: int = None) -> List[schemas.User]:
        with self._session() as session:
            users = session.query(User).filter(User.username.ilike(f'%{username_part}%')).limit(limit)
            return [user_model_as_schema(user) for user in users]


class MessageCRUD:

    def __init__(self, session: Callable[[], Session]):
        self._session = session

    def create(self, message_text: str, from_user_id: int, to_user_id: int) -> schemas.Message:
        with self._session() as session:
            message = Message(message_text=message_text, from_user_id=from_user_id, to_user_id=to_user_id)
            session.add(message)
            session.commit()
            return message_model_as_schema(message)

    def get_by_id(self, message_id: int) -> schemas.Message:
        with self._session() as session:
            message = session.get(Message, message_id)
            if not message:
                raise Exception('message does not exists')
            return message_model_as_schema(message)

    def get_user_dialog(self, user_id: str, with_user_id: int) -> List[schemas.Message]:
        with self._session() as session:
            messages = session.query(Message).\
                filter((Message.from_user_id == user_id) & (Message.to_user_id == with_user_id) |
                       (Message.to_user_id == user_id) & (Message.from_user_id == with_user_id)).all()
            return [message_model_as_schema(message) for message in messages]

    def get_user_dialogs_users_ids(self, user_id: str) -> List[int]:
        with self._session() as session:
            users_ids_incoming: List[tuple] = session.query(Message.from_user_id).distinct(Message.from_user_id).\
                filter(Message.to_user_id == user_id).all()
            users_ids_outgoing: List[tuple] = session.query(Message.to_user_id).distinct(Message.to_user_id).\
                filter(Message.from_user_id == user_id).all()
            users_ids = set(users_ids_incoming)
            users_ids.update(users_ids_outgoing)
            return [user_id[0] for user_id in users_ids]
