from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared SQLAlchemy base."""


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    clinician_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    clinician_language: Mapped[str] = mapped_column(String(10), nullable=False, default="pt-PT")
    patient_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-GB")
    region: Mapped[str] = mapped_column(String(10), nullable=False, default="pt-PT")
    shared_device: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript_purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
