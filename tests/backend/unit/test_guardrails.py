import pytest

from app.schemas.sessions import SoapSummary, TranslationSegment
from app.services.guardrails import GuardrailService
from app.workers.asr_worker import transcribe_audio


def test_guardrail_rejects_missing_translation_text() -> None:
    service = GuardrailService()

    with pytest.raises(ValueError, match="translation text is required"):
        service.validate_translation(
            TranslationSegment(
                segment_id="segment-1",
                source_text="no pain",
                translated_text="",
                is_final=True,
            )
        )


def test_guardrail_rejects_whitespace_only_translation_text() -> None:
    service = GuardrailService()

    with pytest.raises(ValueError, match="translation text is required"):
        service.validate_translation(
            TranslationSegment(
                segment_id="segment-1",
                source_text="no pain",
                translated_text="   ",
                is_final=True,
            )
        )


def test_guardrail_rejects_missing_soap_fields() -> None:
    service = GuardrailService()

    with pytest.raises(ValueError, match="all soap fields are required"):
        service.validate_soap(
            SoapSummary(
                subjective="Patient describes symptoms.",
                objective="",
                assessment="Assessment pending.",
                plan="Plan pending.",
            )
        )


def test_guardrail_rejects_whitespace_only_soap_fields() -> None:
    service = GuardrailService()

    with pytest.raises(ValueError, match="all soap fields are required"):
        service.validate_soap(
            SoapSummary(
                subjective="   ",
                objective="Observation pending.",
                assessment="Assessment pending.",
                plan="Plan pending.",
            )
        )


def test_asr_worker_returns_segment_without_translated_text() -> None:
    segment = transcribe_audio(segment_id="segment-1", chunk=b"audio")

    assert segment.translated_text is None
