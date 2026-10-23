from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WordPressPost:
    """A post retrieved from the WordPress REST API."""

    id: int
    content: str
    published_at: datetime
    status: str
    tag_ids: tuple[int, ...] = ()
    featured_media_id: int = 0