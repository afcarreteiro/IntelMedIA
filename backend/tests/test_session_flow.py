import pytest
from sqlalchemy import delete
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.database import init_db, session_maker
from app.main import app
from app.models.session import Session
from app.schemas.session import SoapResponse
from app.services.asr_pipeline import ASRTranscription, asr_pipeline_service
from app.services.audio_store import audio_chunk_store
from app.services.runpod_asr import runpod_asr_service
from app.services.soap_store import soap_store
from app.services.soap_generation import soap_generation_service
from app.services.transcript_store import transcript_store
from app.services.translation import NLLB_LANGUAGE_CODES
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


def test_translation_uses_nllb_mapping(monkeypatch):
    class FakeTokenizer:
        def __init__(self):
            self.src_lang = None

        def __call__(self, text, return_tensors="pt"):
            return {"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}

        def convert_tokens_to_ids(self, token):
            return 7 if token == "eng_Latn" else 9

        def batch_decode(self, generated_tokens, skip_special_tokens=True):
            return ["Hello there"]

    class FakeModel:
        device = "cpu"

        def generate(self, **kwargs):
            assert kwargs["forced_bos_token_id"] == 7
            return [[7, 8, 9]]

    monkeypatch.setattr(translation_service, "_ensure_model", lambda: (FakeTokenizer(), FakeModel()))
    result = translation_service.translate("Ola", "pt-PT", "en-GB")

    assert NLLB_LANGUAGE_CODES["pt-PT"] == "por_Latn"
    assert result.translated_text == "Hello there"
    assert result.engine == "facebook/nllb-200-distilled-600M"
    assert result.uncertainty_reasons == []


def test_streaming_websocket_emits_partial_and_final(monkeypatch):
    init_db()
    with session_maker() as db:
        db.execute(delete(Session))
        db.commit()

    transcript_store._sessions.clear()
    soap_store._soaps.clear()
    audio_chunk_store._chunks.clear()

    monkeypatch.setattr(asr_pipeline_service, "preload", lambda: (True, None))
    monkeypatch.setattr(
        translation_service,
        "translate",
        lambda source_text, source_language, target_language: TranslationResult(
            translated_text="Good morning",
            engine="mt-stream-test",
            uncertainty_reasons=[],
        ),
    )
    monkeypatch.setattr(translation_service, "preload", lambda: (True, None))

    class FakeRunPodStream:
        def __init__(self, *, on_partial, **_kwargs):
            self.engine_label = "runpod:asr-stream-test"
            self._on_partial = on_partial
            self._partial_emitted = False

        async def send_audio_pcm(self, _payload: bytes):
            if self._partial_emitted:
                return
            self._partial_emitted = True
            await self._on_partial(
                {
                    "type": "partial",
                    "text": "Bom dia",
                    "detected_language": "pt-PT",
                    "is_final": False,
                }
            )

        async def flush(self):
            return {
                "type": "final",
                "text": "Bom dia",
                "detected_language": "pt-PT",
                "is_final": True,
            }

        async def close(self):
            return None

    async def fake_create_stream(**kwargs):
        return FakeRunPodStream(**kwargs)

    monkeypatch.setattr(runpod_asr_service, "create_stream", fake_create_stream)

    with TestClient(app) as client:
        login_response = client.post(
            "/auth/login",
            json={"username": "clinician", "password": "intelmedia"},
        )
        token = login_response.json()["access_token"]

        create_response = client.post(
            "/sessions",
            json={
                "clinician_language": "pt-PT",
                "patient_language": "en-GB",
                "region": "pt-PT",
                "shared_device": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        session_id = create_response.json()["session_id"]

        with client.websocket_connect(f"/ws/sessions/{session_id}/stream") as websocket:
            websocket.send_json(
                {
                    "type": "auth",
                    "token": token,
                    "speaker": "clinician",
                    "source_language": "pt-PT",
                    "translation_language": "en-GB",
                    "sample_rate": 16000,
                }
            )
            first_event = websocket.receive_json()
            assert first_event["type"] == "ready"

            if first_event["type"] == "warning":
                first_event = websocket.receive_json()

            audio_frame = (b"\x20\x20" * 2560)
            websocket.send_bytes(audio_frame)

            event_types: list[str] = []
            for _ in range(4):
                payload = websocket.receive_json()
                event_types.append(payload["type"])
                if payload["type"] == "translation_partial":
                    assert payload["text"] == "Good morning"
                    break

            websocket.send_json({"type": "stop"})

            final_payload = None
            for _ in range(4):
                payload = websocket.receive_json()
                if payload["type"] == "segment_final":
                    final_payload = payload
                    break

            assert "transcript_partial" in event_types
            assert "translation_partial" in event_types
            assert final_payload is not None
            assert final_payload["segment"]["translation_text"] == "Good morning"
