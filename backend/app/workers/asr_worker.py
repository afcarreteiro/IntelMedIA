import time

from app.schemas.sessions import TranslationSegment


def transcribe_audio(segment_id: str, chunk: bytes) -> TranslationSegment:
    return TranslationSegment(
        segment_id=segment_id,
        source_text="stub transcript",
        translated_text=None,
        is_final=False,
    )


def run_worker_loop(sleep_seconds: int = 30, sleep_fn=time.sleep) -> None:
    while True:
        sleep_fn(sleep_seconds)


def main() -> None:
    run_worker_loop()


if __name__ == "__main__":
    main()
