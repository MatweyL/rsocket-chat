from typing import Callable

from sqlalchemy import Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.logs import logger
from app.models import Base

engine: Engine = None
session: Callable[[], Session] = None


def create_session(db_name: str):
    global engine, session
    if not engine:
        logger.warning(f'initializing db {db_name}')
        engine = create_engine(f"sqlite:///{db_name}")
        Base.metadata.create_all(engine)
        session = sessionmaker(engine, expire_on_commit=False)
    else:
        logger.warning(f'db {db_name} already exists')
    return session


def drop_database():
    global engine
    Base.metadata.drop_all(engine)
