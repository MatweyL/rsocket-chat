from app.schemas import GetDialogsRequest, SendMessageRequest, GetDialogMessagesRequest


def test_get_dialog(chat_service, users):
    user1 = users[-1]
    user2 = users[-2]
    user3 = users[-3]
    get_dialogs_request = GetDialogsRequest(user_id=user1.id)
    dialogs = chat_service.get_dialogs(get_dialogs_request)
    assert not dialogs
    request = SendMessageRequest(message_text='test',
                                 from_user_id=user1.id,
                                 to_user_id=user2.id)
    chat_service.send_message(request)
    dialogs = chat_service.get_dialogs(get_dialogs_request)
    assert len(dialogs) == 1
    assert dialogs[0].user.id == user1.id
    assert dialogs[0].with_user.id == user2.id
    request = SendMessageRequest(message_text='test',
                                 from_user_id=user3.id,
                                 to_user_id=user1.id)
    chat_service.send_message(request)

    dialogs = chat_service.get_dialogs(get_dialogs_request)
    assert len(dialogs) == 2
    for dialog in dialogs:
        assert dialog.user.id == user1.id


def test_get_dialog_messages(chat_service, users):
    user1 = users[-1]
    user2 = users[-2]
    get_dialog_messages_request = GetDialogMessagesRequest(user_id=user1.id,
                                                           with_user_id=user2.id)
    messages = chat_service.get_dialog_messages(get_dialog_messages_request)
    assert not messages
    sent_messages = [

        chat_service.send_message(SendMessageRequest(message_text='test 1',
                                                     from_user_id=user1.id,
                                                     to_user_id=user2.id)),
        chat_service.send_message(SendMessageRequest(message_text='test 2',
                                                     from_user_id=user2.id,
                                                     to_user_id=user1.id)),
        chat_service.send_message(SendMessageRequest(message_text='test 3',
                                                     from_user_id=user1.id,
                                                     to_user_id=user2.id)),
        chat_service.send_message(SendMessageRequest(message_text='test 4',
                                                     from_user_id=user2.id,
                                                     to_user_id=user1.id)),
        chat_service.send_message(SendMessageRequest(message_text='test 5',
                                                     from_user_id=user1.id,
                                                     to_user_id=user2.id)),
    ]
    messages = chat_service.get_dialog_messages(get_dialog_messages_request)
    assert len(messages) == len(sent_messages)
