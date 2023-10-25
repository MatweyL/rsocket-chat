from datetime import datetime
from typing import List

import pytest

from app.cruds import UserAccountCRUD, MessageCRUD
from app.database import create_database
from app.models import User
from app.services import AuthService


@pytest.fixture(scope='module')
def session():
    s = create_database(r"D:\University\7_semestr\rksp\practice_04_rsocket\teststest.db")
    return s


@pytest.fixture(scope='module')
def user_account_crud(session):
    return UserAccountCRUD(session=session)


@pytest.fixture(scope='module')
def message_crud(session):
    return MessageCRUD(session=session)


@pytest.fixture(scope='module')
def auth_service(user_account_crud):
    return AuthService(user_account_crud=user_account_crud)


un1 = f"first_{datetime.now()}"
un2 = f"second_{datetime.now()}"
un3 = f"third_{datetime.now()}"
u1: User = None
u2: User = None
u3: User = None

usernames: List[str] = [f"user_{datetime.now()}_{i}" for i in range(10)]
users_list: List[User] = None


@pytest.fixture(scope='module')
def user1(user_account_crud):
    global u1, un1
    if not u1:
        u1 = user_account_crud.create(un1)
    return u1


@pytest.fixture(scope='module')
def user2(user_account_crud):
    global u2, un2
    if not u2:
        u2 = user_account_crud.create(un2)
    return u2


@pytest.fixture(scope='module')
def user3(user_account_crud):
    global u3, un3
    if not u3:
        u3 = user_account_crud.create(un3)
    return u3


@pytest.fixture(scope='module')
def users(user_account_crud):
    global usernames, users_list
    if not users_list:
        users_list = [user_account_crud.create(username) for username in usernames]
    return users_list
