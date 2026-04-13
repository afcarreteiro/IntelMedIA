from pathlib import Path


def test_runtime_compose_references_required_services() -> None:
    compose_path = Path(__file__).resolve().parents[3] / "infra" / "docker-compose.yml"
    compose_content = compose_path.read_text(encoding="utf-8")

    for service_name in (
        "gateway",
        "asr-worker",
        "mt-worker",
        "soap-worker",
        "redis",
        "postgres",
    ):
        assert f"{service_name}:" in compose_content


def test_runtime_mvp_files_align_with_compose_and_local_defaults() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    compose_content = (repo_root / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    alembic_content = (repo_root / "backend" / "alembic.ini").read_text(encoding="utf-8")
    env_content = (repo_root / "infra" / "env" / ".env.example").read_text(encoding="utf-8")
    prometheus_content = (repo_root / "infra" / "prometheus" / "prometheus.yml").read_text(
        encoding="utf-8"
    )

    assert "image: nginx:1.27-alpine" not in compose_content
    assert "uvicorn app.main:app" in compose_content

    for worker_name in ("asr-worker", "mt-worker", "soap-worker"):
        assert f"{worker_name}:" in compose_content
    assert compose_content.count("command:") >= 4
    assert "INTELMEDIA_DATABASE_URL: postgresql+psycopg://intelmedia:intelmedia@postgres:5432/intelmedia" in compose_content
    assert "INTELMEDIA_REDIS_URL: redis://redis:6379/0" in compose_content

    assert "sqlalchemy.url = postgresql+psycopg://intelmedia:intelmedia@localhost:5432/intelmedia" in alembic_content
    assert "INTELMEDIA_DATABASE_URL=postgresql+psycopg://intelmedia:intelmedia@localhost:5432/intelmedia" in env_content
    assert "INTELMEDIA_REDIS_URL=redis://localhost:6379/0" in env_content

    assert "metrics_path: /metrics" in prometheus_content
    assert "gateway:8000" in prometheus_content
