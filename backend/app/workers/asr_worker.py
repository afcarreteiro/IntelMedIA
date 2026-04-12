from app.schemas.sessions import TranslationSegment


def transcribe_audio(segment_id: str, chunk: bytes) -> TranslationSegment:
    return TranslationSegment(
        segment_id=segment_id,
        source_text="stub transcript",
        translated_text=None,
        is_final=False,
    )
