from datetime import UTC, datetime

from app.schemas.sessions import SessionCreateResult, SessionState


def test_session_create_result_defaults_to_idle_state() -> None:
    created = SessionCreateResult(
        session_id="session-123",
        status=SessionState.IDLE,
        created_at=datetime.now(UTC),
    )

    assert created.status is SessionState.IDLE
