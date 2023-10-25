import datetime
from typing import List

from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64))
    load_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r})"


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_text: Mapped[str]
    from_user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    from_user: Mapped["User"] = relationship(primaryjoin=from_user_id == User.id,
                                             lazy='joined')
    to_user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    to_user: Mapped["User"] = relationship(primaryjoin=to_user_id == User.id,
                                           lazy='joined')
    load_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, message_text={self.message_text!r})"

