from fastapi import APIRouter

from app.schemas.sessions import SessionCreateResult
from app.services.sessions import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResult)
def create_session() -> SessionCreateResult:
    return session_service.create_session()


@router.post("/{session_id}/close", response_model=SessionCreateResult)
def close_session(session_id: str) -> SessionCreateResult:
    return session_service.close_session(session_id)
