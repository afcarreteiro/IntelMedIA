import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def test_stream_session_queues_multiple_audio_chunks_for_open_session() -> None:
    client = TestClient(app)
    session_id = client.post("/sessions").json()["session_id"]

    with client.websocket_connect(f"/ws/{session_id}") as websocket:
        websocket.send_bytes(b"pcm-1")
        first_response = websocket.receive_json()

        websocket.send_bytes(b"pcm-2")
        second_response = websocket.receive_json()

    assert first_response["type"] == "audio_queued"
    assert second_response["type"] == "audio_queued"
    assert first_response["message_id"].startswith("audio-")
    assert second_response["message_id"].startswith("audio-")
    assert int(second_response["message_id"].split("-")[1]) == int(
        first_response["message_id"].split("-")[1]
    ) + 1


def test_stream_session_rejects_unknown_session() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/missing-session") as websocket:
        websocket.send_bytes(b"pcm")

        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert exc_info.value.code == 1008


def test_stream_session_rejects_closed_session() -> None:
    client = TestClient(app)
    session_id = client.post("/sessions").json()["session_id"]
    client.post(f"/sessions/{session_id}/close")

    with client.websocket_connect(f"/ws/{session_id}") as websocket:
        websocket.send_bytes(b"pcm")

        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert exc_info.value.code == 1008
