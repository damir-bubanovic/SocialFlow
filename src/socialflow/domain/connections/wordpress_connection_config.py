from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordPressConnectionConfig:
    """Non-secret settings for a WordPress connection."""

    site_url: str
    username: str

    def normalized(self) -> "WordPressConnectionConfig":
        """Return configuration with normalized values."""
        return WordPressConnectionConfig(
            site_url=self.site_url.strip().rstrip("/"),
            username=self.username.strip(),
        )

    def is_complete(self) -> bool:
        """Return whether required connection settings are present."""
        return bool(
            self.site_url.strip()
            and self.username.strip()
        )