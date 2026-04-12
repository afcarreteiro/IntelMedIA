from app.schemas.sessions import TranslationSegment


def translate_segment(segment: TranslationSegment) -> TranslationSegment:
    return segment.model_copy(update={"translated_text": f"translated: {segment.source_text}"})
