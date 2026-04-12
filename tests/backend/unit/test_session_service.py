import tomllib
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import HTTPException, status
from app.models.session_metadata import SessionMetadata
from app.schemas.sessions import SessionCreateResult, SessionState
from app.services.sessions import SessionService
from sqlalchemy.schema import CreateTable


def test_create_session_starts_idle_and_close_transitions_to_closed() -> None:
    service = SessionService()

    created = service.create_session()
    closed = service.close_session(created.session_id)

    assert created.status is SessionState.IDLE
    assert closed.status is SessionState.CLOSED


def test_close_session_preserves_original_created_at_timestamp() -> None:
    service = SessionService()

    created = service.create_session()
    time.sleep(0.02)
    closed = service.close_session(created.session_id)

    assert closed.created_at == created.created_at


def test_close_session_rejects_unknown_session_id() -> None:
    service = SessionService()

    with pytest.raises(HTTPException) as exc_info:
        service.close_session("missing-session")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "session not found"


def test_session_create_result_defaults_to_idle_state() -> None:
    created = SessionCreateResult(
        session_id="session-123",
        status=SessionState.IDLE,
        created_at=datetime.now(UTC),
    )

    assert created.status is SessionState.IDLE


def test_backend_pytest_config_supports_running_from_backend_directory() -> None:
    pyproject_path = Path(__file__).resolve().parents[3] / "backend" / "pyproject.toml"
    config = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    pytest_config = config["tool"]["pytest"]["ini_options"]

    assert pytest_config["pythonpath"] == ["."]
    assert pytest_config["testpaths"] == ["../tests"]


def test_session_metadata_status_column_emits_database_check_constraint() -> None:
    ddl = str(CreateTable(SessionMetadata.__table__).compile())

    assert 'CHECK (status IN (' in ddl
    for state in SessionState:
        assert f"'{state.value}'" in ddl
