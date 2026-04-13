import pytest
from fastapi import HTTPException

from app.logging import redact
from app.services.auth import AuthService


def test_login_returns_bearer_token_for_known_clinician() -> None:
    service = AuthService()

    token = service.login(username="clinician", password="intelmedia")

    assert token.access_token
    assert token.token_type == "bearer"


def test_login_rejects_invalid_credentials_without_echoing_inputs() -> None:
    service = AuthService()

    with pytest.raises(HTTPException) as exc_info:
        service.login(username="clinician", password="wrong-password")

    detail = getattr(exc_info.value, "detail", "")
    assert detail == "invalid credentials"
    assert "clinician" not in detail
    assert "wrong-password" not in detail


def test_redact_masks_non_empty_values_and_preserves_empty_values() -> None:
    assert redact("intelmedia") == "[redacted]"
    assert redact("") == ""
