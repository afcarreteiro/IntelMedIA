import uuid
from datetime import datetime, timezone
from typing import Dict, List

from app.schemas.session import TranscriptSegment


class TranscriptStore:
    """Volatile in-memory transcript store used only during the active session."""

    def __init__(self):
        self._sessions: Dict[str, List[TranscriptSegment]] = {}

    def add_segment(self, session_id: str, segment: TranscriptSegment) -> TranscriptSegment:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(segment)
        return segment

    def create_segment(
        self,
        *,
        speaker: str,
        source_text: str,
        source_language: str,
        translation_text: str,
        translation_language: str,
        source_mode: str,
        is_uncertain: bool,
        uncertainty_reasons: list[str],
        translation_engine: str,
        edited_by_clinician: bool = False,
    ) -> TranscriptSegment:
        now = datetime.now(timezone.utc)
        return TranscriptSegment(
            segment_id=str(uuid.uuid4()),
            speaker=speaker,
            timestamp_ms=int(now.timestamp() * 1000),
            created_at=now.isoformat(),
            source_text=source_text,
            source_language=source_language,
            translation_text=translation_text,
            translation_language=translation_language,
            source_mode=source_mode,
            edited_by_clinician=edited_by_clinician,
            is_uncertain=is_uncertain,
            uncertainty_reasons=uncertainty_reasons,
            translation_engine=translation_engine,
        )

    def update_segment(
        self,
        session_id: str,
        segment_id: str,
        new_text: str,
        translation_text: str,
        is_uncertain: bool,
        uncertainty_reasons: list[str],
        translation_engine: str,
    ) -> TranscriptSegment | None:
        if session_id in self._sessions:
            for segment in self._sessions[session_id]:
                if segment.segment_id == segment_id:
                    segment.source_text = new_text
                    segment.translation_text = translation_text
                    segment.is_uncertain = is_uncertain
                    segment.uncertainty_reasons = uncertainty_reasons
                    segment.translation_engine = translation_engine
                    segment.edited_by_clinician = True
                    return segment
        return None

    def get_session_segments(self, session_id: str) -> List[TranscriptSegment]:
        return list(self._sessions.get(session_id, []))

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]


transcript_store = TranscriptStore()
