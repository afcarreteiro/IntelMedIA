from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from app.schemas.sessions import SessionCreateResult, SessionState


class SessionService:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionCreateResult] = {}

    def create_session(self) -> SessionCreateResult:
        session_id = str(uuid4())
        created = SessionCreateResult(
            session_id=session_id,
            status=SessionState.IDLE,
            created_at=datetime.now(UTC),
        )
        self._sessions[session_id] = created
        return created

    def close_session(self, session_id: str) -> SessionCreateResult:
        created = self._sessions.get(session_id)
        if created is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

        closed = SessionCreateResult(
            session_id=session_id,
            status=SessionState.CLOSED,
            created_at=created.created_at,
        )
        self._sessions[session_id] = closed
        return closed
