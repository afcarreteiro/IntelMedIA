from app.services.orchestrator import Orchestrator


def test_publish_audio_returns_queue_message_id() -> None:
    orchestrator = Orchestrator()

    message_id = orchestrator.publish_audio(session_id="session-123", chunk=b"pcm-bytes")

    assert message_id == "audio-1"
