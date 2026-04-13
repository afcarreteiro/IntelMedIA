from app.schemas.sessions import SoapSummary, TranslationSegment


class GuardrailService:
    def validate_translation(self, segment: TranslationSegment) -> TranslationSegment:
        if not segment.translated_text or not segment.translated_text.strip():
            raise ValueError("translation text is required")
        return segment

    def validate_soap(self, summary: SoapSummary) -> SoapSummary:
        fields = [
            summary.subjective,
            summary.objective,
            summary.assessment,
            summary.plan,
        ]
        if not all(isinstance(field, str) and field.strip() for field in fields):
            raise ValueError("all soap fields are required")
        return summary
