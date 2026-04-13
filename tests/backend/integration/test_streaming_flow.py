import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def test_stream_session_queues_one_audio_chunk_and_closes() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/session-123") as websocket:
        websocket.send_bytes(b"pcm-bytes")
        response = websocket.receive_json()

        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert response == {"type": "audio_queued", "message_id": "audio-1"}
    assert exc_info.value.code == 1000


def test_stream_session_response_does_not_expose_raw_audio_payload() -> None:
    client = TestClient(app)
    secret_audio_chunk = b"patient-sensitive-audio"

    with client.websocket_connect("/ws/session-privacy") as websocket:
        websocket.send_bytes(secret_audio_chunk)
        response = websocket.receive_json()

    assert response["type"] == "audio_queued"
    assert "chunk" not in response
    assert "payload" not in response
