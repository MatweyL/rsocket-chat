from datetime import datetime

import pytest

username = f"first_{datetime.now()}"


def test_user_creation(user_account_crud):
    user = user_account_crud.create(username)
    assert user.username == username
    with pytest.raises(Exception):
        user_account_crud.create(username)


def test_user_getting(user_account_crud):
    username_2 = username + '1'
    user_account_crud.create(username_2)
    user = user_account_crud.get_by_username(username_2)
    assert user.username == username_2

    with pytest.raises(Exception):
        user_account_crud.get_by_username(username_2 + '1')


def test_user_finding_by_username_part(user_account_crud):
    datetime_now_str = str(datetime.now())
    username1 = f'Vasua_{datetime_now_str}'
    username2 = f'Vasilisa_{datetime_now_str}'
    username3 = f'Vanua_{datetime_now_str}'
    username4 = f'Vitaliy_{datetime_now_str}'
    username5 = f'Viktoria_{datetime_now_str}'
    usernames = [username1, username2, username3, username4, username5]
    users = [user_account_crud.create(username) for username in usernames]
    found_users = user_account_crud.find_by_username_part('V', 1)
    assert len(found_users) == 1
    found_users = user_account_crud.find_by_username_part(datetime_now_str)
    assert len(found_users) == len(users)
    limit = 3
    found_users = user_account_crud.find_by_username_part(datetime_now_str, limit)
    assert len(found_users) == limit
    limit = 2
    found_users = user_account_crud.find_by_username_part('vas', limit)
    assert len(found_users) == 2
    found_usernames = ('Vasua', 'Vasilisa')
    for found_user in found_users:
        for found_username in found_usernames:
            if found_username in found_user.username:
                break
        else:
            raise Exception(f'wrong found user: {found_user.username} not in {found_usernames}')
