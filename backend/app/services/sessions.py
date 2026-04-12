from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from app.schemas.sessions import SessionCreateResult, SessionState
from app.services.cleanup import CleanupService


class SessionService:
    def __init__(self, cleanup_service: CleanupService | None = None) -> None:
        self._sessions: dict[str, SessionCreateResult] = {}
        self.cleanup_service = cleanup_service or CleanupService()

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

    def delete_session(self, session_id: str) -> dict[str, str]:
        created = self._sessions.get(session_id)
        if created is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

        self._sessions.pop(session_id)
        return self.cleanup_service.delete_session(session_id)
