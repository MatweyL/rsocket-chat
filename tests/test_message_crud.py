def test_message_creation(user_account_crud, message_crud, user1, user2):
    message = message_crud.create('test', user1.id, user2.id)
    assert message.from_user.username == user1.username
    assert message.to_user.username == user2.username

    message_from_db = message_crud.get_by_id(message.id)
    assert message.message_text == message_from_db.message_text

    messages = [message,
                message_crud.create('1', user1.id, user2.id),
                message_crud.create('2', user2.id, user1.id),
                message_crud.create('3', user1.id, user2.id),
                message_crud.create('4', user2.id, user1.id)]

    dialog_messages = message_crud.get_user_dialog(user1.id, user2.id)
    for message, dialog_message in zip(messages, dialog_messages):
        assert message.id == dialog_message.id


def test_dialogs_getting(user_account_crud, message_crud, users):
    user1 = users[0]
    user2 = users[1]
    user3 = users[2]
    user4 = users[3]

    message_crud.create('to user1 #1', user2.id, user1.id)
    message_crud.create('to user1 #2', user2.id, user1.id)
    message_crud.create('to user1 #3', user2.id, user1.id)
    message_crud.create('to user1 #4', user3.id, user1.id)
    dialogs = message_crud.get_user_dialogs_users_ids(user1.id)
    assert len(dialogs) == 2
    assert isinstance(dialogs[-1], int)

    message_crud.create('to user2 #5', user1.id, user2.id)
    dialogs = message_crud.get_user_dialogs_users_ids(user1.id)
    assert len(dialogs) == 2
    users_ids = {user2.id, user3.id}
    for dialog_user_id in dialogs:
        assert dialog_user_id in users_ids

    message_crud.create('to user4 #6', user1.id, user4.id)
    dialogs = message_crud.get_user_dialogs_users_ids(user1.id)
    users_ids.add(user4.id)
    assert len(dialogs) == 3
    for dialog_user_id in dialogs:
        assert dialog_user_id in users_ids
    message_crud.create('to user1 #7', user4.id, user1.id)
    dialogs = message_crud.get_user_dialogs_users_ids(user1.id)
    assert len(dialogs) == 3
