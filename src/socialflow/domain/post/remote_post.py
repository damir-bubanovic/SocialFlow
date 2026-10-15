from dataclasses import dataclass
from datetime import datetime

from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


@dataclass(frozen=True, slots=True)
class RemotePost:
    """A published post retrieved from an external platform."""

    remote_id: str
    destination: PublishingDestination
    content: str
    published_at: datetime
    status: str