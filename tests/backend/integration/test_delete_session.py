from app.services.cleanup import CleanupService


def test_delete_session_returns_deleted_session_id() -> None:
    service = CleanupService()

    deleted = service.delete_session("session-123")

    assert deleted == {"deleted_session_id": "session-123"}
