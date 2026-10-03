from enum import StrEnum


class Language(StrEnum):
    """Languages supported for SocialFlow post content."""

    CROATIAN = "HR"
    ENGLISH = "EN"

    @property
    def display_name(self) -> str:
        """Return the human-readable language name."""
        if self is Language.CROATIAN:
            return "Croatian"

        return "English"

    @property
    def label(self) -> str:
        """Return the language label used by the UI."""
        return f"{self.value} - {self.display_name}"