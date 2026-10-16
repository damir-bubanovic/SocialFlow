import pytest

from typing import Any
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


def test_wordpress_tag_preserves_id_and_normalizes_name() -> None:
    tag = WordPressTag(id=42, name="  SocialFlow  ")

    assert tag.id == 42
    assert tag.name == "SocialFlow"


@pytest.mark.parametrize(
    "invalid_id",
    [
        0,
        -1,
        -100,
        True,
        False,
        "42",
        42.0,
        None,
    ],
)
def test_wordpress_tag_rejects_invalid_ids(invalid_id) -> None:
    with pytest.raises(
        ValueError,
        match="WordPress tag ID must be a positive integer.",
    ):
        WordPressTag(id=invalid_id, name="Python")


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_wordpress_tag_rejects_empty_names(invalid_name) -> None:
    with pytest.raises(ValueError, match="tag name"):
        WordPressTag(id=42, name=invalid_name)

@pytest.mark.parametrize(
    "invalid_name",
    [
        None,
        123,
        True,
        [],
        {},
    ],
)
def test_wordpress_tag_rejects_non_string_names(
    invalid_name: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match="WordPress tag name must be a non-empty string.",
    ):
        WordPressTag(id=42, name=invalid_name)

@pytest.mark.parametrize(
    ("original_name", "expected_name"),
    [
        ("  Hrvatska  ", "Hrvatska"),
        ("  Čakovec  ", "Čakovec"),
        ("  čćžšđ  ", "čćžšđ"),
        ("  ČĆŽŠĐ  ", "ČĆŽŠĐ"),
        ("  Croatian & English  ", "Croatian & English"),
        ("  Python 3.12  ", "Python 3.12"),
        ("  日本語  ", "日本語"),
        ("  café  ", "café"),
        ("\tSocialFlow\n", "SocialFlow"),
    ],
)
def test_wordpress_tag_preserves_unicode_and_normalizes_whitespace(
    original_name: str,
    expected_name: str,
) -> None:
    tag = WordPressTag(id=42, name=original_name)

    assert tag.id == 42
    assert tag.name == expected_name