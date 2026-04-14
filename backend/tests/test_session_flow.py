import pytest
from sqlalchemy import delete
from httpx import ASGITransport, AsyncClient

from app.database import init_db, session_maker
from app.main import app
from app.models.session import Session
from app.schemas.session import SoapResponse
from app.services.asr_pipeline import ASRTranscription, asr_pipeline_service
from app.services.audio_store import audio_chunk_store
from app.services.soap_store import soap_store
from app.services.soap_generation import soap_generation_service
from app.services.transcript_store import transcript_store
from app.services.translation import TranslationResult, translation_service


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_session_flow_end_to_end(monkeypatch):
    init_db()
    with session_maker() as db:
        db.execute(delete(Session))
        db.commit()

    transcript_store._sessions.clear()
    soap_store._soaps.clear()
    audio_chunk_store._chunks.clear()

    monkeypatch.setattr(
        asr_pipeline_service,
        "transcribe_merged_chunks",
        lambda chunks, language_code: ASRTranscription(
            text="Onde e a dor?",
            detected_language=language_code,
            engine="asr-test",
            uncertainty_reasons=[],
        ),
    )
    monkeypatch.setattr(
        translation_service,
        "translate",
        lambda source_text, source_language, target_language: TranslationResult(
            translated_text="Where is the pain?",
            engine="mt-test",
            uncertainty_reasons=[],
        ),
    )
    monkeypatch.setattr(
        soap_generation_service,
        "build",
        lambda session_id, segments: SoapResponse(
            session_id=session_id,
            subjective="Resumo subjetivo",
            objective="Resumo objetivo",
            assessment="Avaliacao clinica pendente.",
            plan="Plano sob revisao clinica.",
            generated_at="",
            review_required=True,
            retention_notice="Sem retencao persistente.",
        ),
    )

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

        audio_response = await client.post(
            f"/sessions/{session_id}/audio-chunks",
            json={
                "chunk_id": "chunk-1",
                "sequence": 0,
                "started_at_ms": 1000,
                "ended_at_ms": 2400,
                "duration_ms": 1400,
                "overlap_ms": 450,
                "sample_rate": 16000,
                "payload_base64": "AAAA",
            },
            headers=headers,
        )
        assert audio_response.status_code == 202
        assert audio_response.json()["accepted"] is True

        finalize_response = await client.post(
            f"/sessions/{session_id}/audio-utterances/finalize",
            json={
                "speaker": "clinician",
                "source_language": "pt-PT",
                "translation_language": "en-GB",
            },
            headers=headers,
        )
        assert finalize_response.status_code == 201
        finalize_payload = finalize_response.json()
        assert finalize_payload["transcript_text"] == "Onde e a dor?"
        assert finalize_payload["segment"]["translation_text"] == "Where is the pain?"
        assert finalize_payload["segment"]["source_mode"] == "speech"

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
