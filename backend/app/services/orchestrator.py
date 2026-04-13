from app.redis_client import RedisClient


class Orchestrator:
    def __init__(self, redis_client: RedisClient | None = None) -> None:
        self.redis_client = redis_client or RedisClient()

    def publish_audio(self, session_id: str, chunk: bytes) -> str:
        return self.redis_client.publish_audio(session_id=session_id, chunk=chunk)
