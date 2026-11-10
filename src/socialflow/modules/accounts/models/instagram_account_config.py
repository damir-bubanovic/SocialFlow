from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstagramAccountConfig:
    """Non-secret configuration for an Instagram account."""

    instagram_user_id: str
    username: str

    def normalized(self) -> "InstagramAccountConfig":
        """Return configuration with trimmed values."""
        return InstagramAccountConfig(
            instagram_user_id=self.instagram_user_id.strip(),
            username=self.username.strip(),
        )

    def is_complete(self) -> bool:
        """Return whether the required Instagram user ID is present."""
        return bool(self.instagram_user_id.strip())