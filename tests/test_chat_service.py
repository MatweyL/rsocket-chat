def test_get_dialog(chat_service, users):
    user1 = users[-1]
    user2 = users[-2]
    user3 = users[-3]
    dialogs = chat_service.get_dialogs(user1.id)
    assert not dialogs
    chat_service.send_message('test', user1.id, user2.id)
    dialogs = chat_service.get_dialogs(user1.id)
    assert len(dialogs) == 1
    assert dialogs[0].user.id == user1.id
    assert dialogs[0].with_user.id == user2.id
    chat_service.send_message('test', user3.id, user1.id)

    dialogs = chat_service.get_dialogs(user1.id)
    assert len(dialogs) == 2
    for dialog in dialogs:
        assert dialog.user.id == user1.id


def test_get_dialog_messages(chat_service, users):
    user1 = users[-1]
    user2 = users[-2]
    messages = chat_service.get_dialog_messages(user1.id, user2.id)
    assert not messages
    sent_messages = [
        chat_service.send_message('Hello!', user1.id, user2.id),
        chat_service.send_message('Hello, my friend!', user2.id, user1.id),
        chat_service.send_message('How are you?', user2.id, user1.id),
        chat_service.send_message('I\'m fine, and you?', user1.id, user2.id),
        chat_service.send_message('I\'m fine too)', user1.id, user2.id),
    ]
    messages = chat_service.get_dialog_messages(user1.id, user2.id)
    assert len(messages) == len(sent_messages)

