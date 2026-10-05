from datetime import datetime

from socialflow.application.time.clock import Clock


class SystemClock(Clock):
    """Clock using the system's current local time."""

    def now(self) -> datetime:
        """Return the current local date and time."""
        return datetime.now()