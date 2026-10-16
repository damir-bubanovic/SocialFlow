from socialflow.infrastructure.wordpress.wordpress_tag_name_normalizer import (
    WordPressTagNameNormalizer,
)


def test_normalize_accepts_canonically_equivalent_unicode() -> None:
    assert WordPressTagNameNormalizer.normalize(
        "Čakovec"
    ) == WordPressTagNameNormalizer.normalize(
        "C\u030Cakovec"
    )


def test_normalize_ignores_capitalization() -> None:
    assert WordPressTagNameNormalizer.normalize(
        "SocialFlow"
    ) == WordPressTagNameNormalizer.normalize(
        "socialflow"
    )


def test_normalize_preserves_different_unicode_letters() -> None:
    assert WordPressTagNameNormalizer.normalize(
        "Čakovec"
    ) != WordPressTagNameNormalizer.normalize(
        "Ćakovec"
    )


def test_normalize_supports_unicode_casefold_expansion() -> None:
    assert WordPressTagNameNormalizer.normalize(
        "Straße"
    ) == WordPressTagNameNormalizer.normalize(
        "STRASSE"
    )

def test_normalize_does_not_silently_strip_whitespace() -> None:
    assert WordPressTagNameNormalizer.normalize(
        " SocialFlow "
    ) != WordPressTagNameNormalizer.normalize(
        "SocialFlow"
    )