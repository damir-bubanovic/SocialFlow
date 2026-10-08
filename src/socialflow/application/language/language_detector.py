
import re

from socialflow.domain.language.language import Language


class LanguageDetector:
    """Detect Croatian or English when sufficient evidence exists."""

    _CROATIAN_CHARACTERS = frozenset("čćđšžČĆĐŠŽ")

    _CROATIAN_WORDS = frozenset({
        "ako", "ali", "danas", "da", "dobar", "dobro",
        "godina", "ima", "imamo", "iz", "je", "jedan",
        "kako", "koji", "koja", "moze", "možemo",
        "na", "nova", "novi", "novo", "objava",
        "objavljujemo", "od", "ovo", "sada", "se",
        "smo", "su", "sutra", "to", "u", "vijest",
        "za",
    })

    _ENGLISH_WORDS = frozenset({
        "about", "after", "and", "are", "can",
        "for", "from", "have", "hello", "important",
        "in", "is", "new", "news", "of",
        "on", "our", "post", "publishing", "the",
        "this", "today", "tomorrow", "we", "with",
        "you",
    })

    _MINIMUM_MATCHES = 2

    def detect(self, text: str) -> Language | None:
        """Return the detected language or None when uncertain."""
        if not text.strip():
            return None

        words = re.findall(r"[^\W\d_]+", text.casefold())

        croatian_matches = sum(
            word in self._CROATIAN_WORDS
            for word in words
        )
        english_matches = sum(
            word in self._ENGLISH_WORDS
            for word in words
        )

        has_croatian_characters = any(
            character in self._CROATIAN_CHARACTERS
            for character in text
        )

        if has_croatian_characters and english_matches == 0:
            return Language.CROATIAN

        if (
            croatian_matches >= self._MINIMUM_MATCHES
            and croatian_matches > english_matches
        ):
            return Language.CROATIAN

        if (
            english_matches >= self._MINIMUM_MATCHES
            and english_matches > croatian_matches
        ):
            return Language.ENGLISH

        return None
