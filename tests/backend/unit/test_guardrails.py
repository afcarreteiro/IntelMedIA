import pytest

from app.schemas.sessions import TranslationSegment
from app.services.guardrails import GuardrailService


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
