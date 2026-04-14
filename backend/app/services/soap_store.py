from datetime import datetime, timezone
from typing import Dict, Optional


class SoapStore:
    """In-memory SOAP storage used after session closure."""

    def __init__(self):
        self._soaps: Dict[str, dict] = {}

    def set_soap(self, session_id: str, soap: dict) -> None:
        self._soaps[session_id] = {
            **soap,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready",
        }

    def get_soap(self, session_id: str) -> Optional[dict]:
        return self._soaps.get(session_id)

    def clear_session(self, session_id: str) -> None:
        if session_id in self._soaps:
            del self._soaps[session_id]


soap_store = SoapStore()
