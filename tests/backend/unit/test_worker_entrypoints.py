import pytest

from app.workers import asr_worker, mt_worker, soap_worker


@pytest.mark.parametrize("worker_module", [asr_worker, mt_worker, soap_worker])
def test_worker_entrypoints_run_long_lived_loop(worker_module) -> None:
    calls = 0

    def stop_after_one_sleep(_: int) -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("stop-loop")

    with pytest.raises(RuntimeError, match="stop-loop"):
        worker_module.run_worker_loop(sleep_seconds=0, sleep_fn=stop_after_one_sleep)

    assert calls == 1
