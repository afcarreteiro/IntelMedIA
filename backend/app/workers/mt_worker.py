import time

from app.schemas.sessions import TranslationSegment


def translate_segment(segment: TranslationSegment) -> TranslationSegment:
    return segment.model_copy(update={"translated_text": f"translated: {segment.source_text}"})


def run_worker_loop(sleep_seconds: int = 30, sleep_fn=time.sleep) -> None:
    while True:
        sleep_fn(sleep_seconds)


def main() -> None:
    run_worker_loop()


if __name__ == "__main__":
    main()
