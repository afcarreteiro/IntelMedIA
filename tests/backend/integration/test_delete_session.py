from fastapi.testclient import TestClient

from app.main import app


def test_delete_session_endpoint_returns_deleted_session_id() -> None:
    client = TestClient(app)

    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    response = client.delete(f"/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json() == {"deleted_session_id": session_id}


def test_delete_session_endpoint_returns_404_for_unknown_session_id() -> None:
    client = TestClient(app)

    response = client.delete("/sessions/missing-session")

    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}
