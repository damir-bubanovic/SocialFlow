from datetime import datetime

from socialflow.infrastructure.time.system_clock import SystemClock


def test_system_clock_returns_current_datetime() -> None:
    clock = SystemClock()

    before = datetime.now()
    current = clock.now()
    after = datetime.now()

    assert before <= current <= after