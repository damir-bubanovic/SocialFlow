from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """Provide the current date and time."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current date and time."""