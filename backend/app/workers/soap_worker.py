import time

from app.schemas.sessions import SoapSummary


def generate_soap() -> SoapSummary:
    return SoapSummary(
        subjective="Patient describes symptoms.",
        objective="Observation pending.",
        assessment="Assessment pending.",
        plan="Plan pending.",
    )


def run_worker_loop(sleep_seconds: int = 30, sleep_fn=time.sleep) -> None:
    while True:
        sleep_fn(sleep_seconds)


def main() -> None:
    run_worker_loop()


if __name__ == "__main__":
    main()
