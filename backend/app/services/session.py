from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.session import Session as SessionModel
from app.schemas.session import SessionCreateRequest


class SessionService:
    def __init__(self, db: DbSession):
        self.db = db

    def create_session(self, clinician_id: str, request: SessionCreateRequest) -> SessionModel:
        session = SessionModel(
            clinician_id=clinician_id,
            status="ACTIVE",
            clinician_language=request.clinician_language,
            patient_language=request.patient_language,
            region=request.region,
            shared_device=request.shared_device,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        result = self.db.execute(select(SessionModel).where(SessionModel.id == session_id))
        return result.scalar_one_or_none()

    def get_session_by_clinician(self, clinician_id: str) -> Optional[SessionModel]:
        result = self.db.execute(
            select(SessionModel).where(
                SessionModel.clinician_id == clinician_id,
                SessionModel.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none()

    def close_session(self, session_id: str) -> Optional[SessionModel]:
        session = self.get_session(session_id)
        if session:
            session.status = "CLOSED"
            session.ended_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
        return session

    def mark_transcript_purged(self, session_id: str) -> Optional[SessionModel]:
        session = self.get_session(session_id)
        if session:
            session.transcript_purged_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
