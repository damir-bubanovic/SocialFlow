import unicodedata


class WordPressTagNameNormalizer:
    """Provide consistent WordPress tag name comparison keys."""

    @staticmethod
    def normalize(name: str) -> str:
        """Normalize Unicode and ignore capitalization."""
        return unicodedata.normalize("NFC", name).casefold()