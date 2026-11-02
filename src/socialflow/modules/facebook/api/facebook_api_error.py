
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FacebookApiError(Exception):
    """A structured failure returned by the Facebook Graph API."""

    message: str
    status_code: int | None = None
    code: int | None = None
    subcode: int | None = None
    is_transient: bool = False
    error_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "Facebook API error message must be non-empty."
            )

        for field_name in ("status_code", "code", "subcode"):
            value = getattr(self, field_name)
            if value is not None and type(value) is not int:
                raise ValueError(
                    f"Facebook API {field_name} must be an integer."
                )

        if type(self.is_transient) is not bool:
            raise ValueError(
                "Facebook API is_transient must be a boolean."
            )

        if (
            self.error_type is not None
            and not isinstance(self.error_type, str)
        ):
            raise ValueError(
                "Facebook API error type must be a string or None."
            )

        object.__setattr__(self, "message", self.message.strip())

    def __str__(self) -> str:
        """Return a safe, concise error description."""
        parts = ["Facebook API request failed"]

        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")

        if self.code is not None:
            parts.append(f"code {self.code}")

        if self.subcode is not None:
            parts.append(f"subcode {self.subcode}")

        return " (" + ", ".join(parts) + ")."
