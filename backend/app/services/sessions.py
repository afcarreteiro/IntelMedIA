from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.sessions import SessionCreateResult, SessionState


class SessionService:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def create_session(self) -> SessionCreateResult:
        session_id = str(uuid4())
        self._sessions[session_id] = SessionState.IDLE
        return SessionCreateResult(
            session_id=session_id,
            status=SessionState.IDLE,
            created_at=datetime.now(UTC),
        )

    def close_session(self, session_id: str) -> SessionCreateResult:
        self._sessions[session_id] = SessionState.CLOSED
        return SessionCreateResult(
            session_id=session_id,
            status=SessionState.CLOSED,
            created_at=datetime.now(UTC),
        )
