import time

from fastapi.testclient import TestClient

from app.main import app


def test_login_endpoint_returns_bearer_token_for_known_clinician() -> None:
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"username": "clinician", "password": "intelmedia"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "token_type"}
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_session_lifecycle_endpoints_create_idle_session_and_close_it() -> None:
    client = TestClient(app)

    create_response = client.post("/sessions")

    assert create_response.status_code == 200
    created_body = create_response.json()
    assert created_body["session_id"]
    assert created_body["status"] == "IDLE"
    assert created_body["created_at"]

    time.sleep(0.02)
    close_response = client.post(f"/sessions/{created_body['session_id']}/close")

    assert close_response.status_code == 200
    closed_body = close_response.json()
    assert closed_body["session_id"] == created_body["session_id"]
    assert closed_body["status"] == "CLOSED"
    assert closed_body["created_at"] == created_body["created_at"]


def test_close_session_endpoint_returns_404_for_unknown_session_id() -> None:
    client = TestClient(app)

    response = client.post("/sessions/missing-session/close")

    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}


def test_login_endpoint_rejects_invalid_credentials_without_leaking_inputs() -> None:
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"username": "clinician", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid credentials"}
