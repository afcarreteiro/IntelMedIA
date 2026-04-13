from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.schemas.sessions import SessionState


class SessionMetadata(Base):
    __tablename__ = "session_metadata"

    session_id_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[SessionState] = mapped_column(
        Enum(SessionState, native_enum=False, create_constraint=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
