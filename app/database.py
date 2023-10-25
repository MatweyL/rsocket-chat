import logging
from typing import Callable

from sqlalchemy import Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base

engine: Engine = None
session: Callable[[], Session] = None


def create_database(db_name: str):
    global engine, session
    if not engine:
        logging.warning(f'creating db {db_name}')
        engine = create_engine(f"sqlite:///{db_name}")
        Base.metadata.create_all(engine)
        session = sessionmaker(engine, expire_on_commit=False)
    else:
        logging.warning(f'db {db_name} already exists')
    return session


def drop_database():
    global engine
    Base.metadata.drop_all(engine)
