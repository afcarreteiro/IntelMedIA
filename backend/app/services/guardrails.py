from app.schemas.sessions import SoapSummary, TranslationSegment


class GuardrailService:
    def validate_translation(self, segment: TranslationSegment) -> TranslationSegment:
        if not segment.translated_text:
            raise ValueError("translation text is required")
        return segment

    def validate_soap(self, summary: SoapSummary) -> SoapSummary:
        if not all([summary.subjective, summary.objective, summary.assessment, summary.plan]):
            raise ValueError("all soap fields are required")
        return summary
