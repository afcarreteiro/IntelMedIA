class RedisClient:
    def __init__(self) -> None:
        self.audio_messages: list[dict[str, object]] = []

    def publish_audio(self, session_id: str, chunk: bytes) -> str:
        message_id = f"audio-{len(self.audio_messages) + 1}"
        self.audio_messages.append(
            {"id": message_id, "session_id": session_id, "chunk": chunk}
        )
        return message_id
