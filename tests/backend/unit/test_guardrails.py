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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subjective", "\n\t"),
        ("objective", "\r\n"),
        ("assessment", "   \n"),
        ("plan", "\t"),
    ],
)
def test_guardrail_rejects_control_character_only_soap_fields(field: str, value: str) -> None:
    service = GuardrailService()
    payload = {
        "subjective": "Patient describes symptoms.",
        "objective": "Observation pending.",
        "assessment": "Assessment pending.",
        "plan": "Plan pending.",
    }
    payload[field] = value

    with pytest.raises(ValueError, match="all soap fields are required"):
        service.validate_soap(SoapSummary(**payload))


def test_guardrail_rejects_soap_payload_with_null_field() -> None:
    service = GuardrailService()
    invalid_summary = SoapSummary.model_construct(
        subjective=None,
        objective="Observation pending.",
        assessment="Assessment pending.",
        plan="Plan pending.",
    )

    with pytest.raises(ValueError, match="all soap fields are required"):
        service.validate_soap(invalid_summary)


def test_asr_worker_returns_segment_without_translated_text() -> None:
    segment = transcribe_audio(segment_id="segment-1", chunk=b"audio")

    assert segment.translated_text is None
