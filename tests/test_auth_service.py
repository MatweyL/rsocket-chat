

def test_register(auth_service, user1):
    unique_username = user1.username + '_1'
    response = auth_service.register(unique_username)
    assert response.success
    assert response.user.username == unique_username

    response = auth_service.register(user1.username)
    assert not response.success
    assert response.error


def test_auth(auth_service, user1):
    response = auth_service.auth(user1.username)
    assert response.success
    assert response.user.id == user1.id

    does_not_existing_username = user1.username + str(hash(123))
    response = auth_service.auth(does_not_existing_username)
    assert not response.success
    assert response.error
