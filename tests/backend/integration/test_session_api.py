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

    close_response = client.post(f"/sessions/{created_body['session_id']}/close")

    assert close_response.status_code == 200
    closed_body = close_response.json()
    assert closed_body["session_id"] == created_body["session_id"]
    assert closed_body["status"] == "CLOSED"
    assert closed_body["created_at"]
