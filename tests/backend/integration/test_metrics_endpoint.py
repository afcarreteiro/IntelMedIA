from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_prometheus_text_payload() -> None:
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# HELP intelmedia_gateway_up" in response.text
    assert "# TYPE intelmedia_gateway_up gauge" in response.text
    assert "intelmedia_gateway_up 1" in response.text
