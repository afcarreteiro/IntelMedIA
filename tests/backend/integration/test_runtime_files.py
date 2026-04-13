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
