from collections import deque
from typing import Deque, Dict, List


class AudioChunkStore:
    """Ephemeral audio chunk storage for session-level utterances."""

    def __init__(self):
        self._chunks: Dict[str, Deque[dict]] = {}
        self._max_chunks_per_session = 48

    def add_chunk(self, session_id: str, chunk: dict) -> dict:
        if session_id not in self._chunks:
            self._chunks[session_id] = deque(maxlen=self._max_chunks_per_session)
        self._chunks[session_id].append(chunk)
        return chunk

    def get_session_chunks(self, session_id: str) -> List[dict]:
        return list(self._chunks.get(session_id, []))

    def drain_session(self, session_id: str) -> List[dict]:
        chunks = self.get_session_chunks(session_id)
        self.clear_session(session_id)
        return chunks

    def clear_session(self, session_id: str) -> None:
        if session_id in self._chunks:
            del self._chunks[session_id]


audio_chunk_store = AudioChunkStore()
