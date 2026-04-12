import tomllib
from datetime import UTC, datetime
from pathlib import Path

from app.models.session_metadata import SessionMetadata
from app.schemas.sessions import SessionCreateResult, SessionState
from sqlalchemy.schema import CreateTable


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
