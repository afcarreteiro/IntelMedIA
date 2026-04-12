from app.services.auth import AuthService


def test_login_returns_bearer_token_for_known_clinician() -> None:
    service = AuthService()

    token = service.login(username="clinician", password="intelmedia")

    assert token.access_token
    assert token.token_type == "bearer"
