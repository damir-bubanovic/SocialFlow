from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordPressMedia:
    """Media information returned by WordPress after an upload."""

    media_id: int
    source_url: str