from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SessionState(StrEnum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


class SessionCreateResult(BaseModel):
    session_id: str
    status: SessionState
    created_at: datetime
