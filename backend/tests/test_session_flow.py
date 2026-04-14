import pytest
from sqlalchemy import delete
from httpx import ASGITransport, AsyncClient

from app.database import init_db, session_maker
from app.main import app
from app.models.session import Session
from app.services.soap_store import soap_store
from app.services.transcript_store import transcript_store


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_session_flow_end_to_end():
    init_db()
    with session_maker() as db:
        db.execute(delete(Session))
        db.commit()

    transcript_store._sessions.clear()
    soap_store._soaps.clear()

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_response = await client.post(
            "/auth/login",
            json={"username": "clinician", "password": "intelmedia"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/sessions",
            json={
                "clinician_language": "pt-PT",
                "patient_language": "en-GB",
                "region": "pt-PT",
                "shared_device": True,
            },
            headers=headers,
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]

        segment_response = await client.post(
            f"/sessions/{session_id}/segments",
            json={
                "speaker": "clinician",
                "source_text": "Onde e a dor?",
                "source_language": "pt-PT",
                "translation_language": "en-GB",
                "source_mode": "typed",
            },
            headers=headers,
        )
        assert segment_response.status_code == 201
        assert segment_response.json()["translation_text"] == "Where is the pain?"

        close_response = await client.post(
            f"/sessions/{session_id}/close",
            headers=headers,
        )
        assert close_response.status_code == 200
        close_payload = close_response.json()
        assert close_payload["session"]["status"] == "CLOSED"
        assert "subjective" in close_payload["soap"]

        transcript_response = await client.get(
            f"/sessions/{session_id}/transcript",
            headers=headers,
        )
        assert transcript_response.status_code == 200
        assert transcript_response.json()["segments"] == []
