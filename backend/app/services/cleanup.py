class CleanupService:
    def delete_session(self, session_id: str) -> dict[str, str]:
        return {"deleted_session_id": session_id}
