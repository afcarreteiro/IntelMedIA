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
