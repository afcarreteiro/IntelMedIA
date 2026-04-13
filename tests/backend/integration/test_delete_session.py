from fastapi.testclient import TestClient

from app.main import app


def test_delete_session_endpoint_returns_deleted_session_id() -> None:
    client = TestClient(app)

    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    response = client.delete(f"/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json() == {"deleted_session_id": session_id}


def test_delete_session_endpoint_response_omits_internal_session_fields() -> None:
    client = TestClient(app)

    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    response = client.delete(f"/sessions/{session_id}")
    body = response.json()

    assert response.status_code == 200
    assert set(body.keys()) == {"deleted_session_id"}


def test_delete_session_endpoint_returns_404_for_unknown_session_id() -> None:
    client = TestClient(app)

    response = client.delete("/sessions/missing-session")

    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}


def test_delete_session_endpoint_404_message_does_not_echo_requested_session_id() -> None:
    client = TestClient(app)
    missing_session_id = "patient-session-123"

    response = client.delete(f"/sessions/{missing_session_id}")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail == "session not found"
    assert missing_session_id not in detail
