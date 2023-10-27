from app.schemas import RegisterRequest, LoginRequest


def test_register(auth_service, user1):
    unique_username = user1.username + '_1'
    request = RegisterRequest(username=unique_username)
    response = auth_service.register(request)
    assert response.success
    assert response.user.username == unique_username

    response = auth_service.register(user1.username)
    assert not response.success
    assert response.error


def test_auth(auth_service, user1):
    request = LoginRequest(username=user1.username)
    response = auth_service.auth(request)
    assert response.success
    assert response.user.id == user1.id

    does_not_existing_username = user1.username + str(hash(123))
    request = LoginRequest(username=does_not_existing_username)
    response = auth_service.auth(request)
    assert not response.success
    assert response.error
