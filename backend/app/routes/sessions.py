from fastapi import APIRouter

from app.schemas.sessions import SessionCreateResult
from app.services.sessions import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])
service = SessionService()


@router.post("", response_model=SessionCreateResult)
def create_session() -> SessionCreateResult:
    return service.create_session()


@router.post("/{session_id}/close", response_model=SessionCreateResult)
def close_session(session_id: str) -> SessionCreateResult:
    return service.close_session(session_id)
