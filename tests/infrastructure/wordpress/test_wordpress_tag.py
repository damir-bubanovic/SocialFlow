import pytest

from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


def test_wordpress_tag_preserves_id_and_normalizes_name() -> None:
    tag = WordPressTag(id=42, name="  SocialFlow  ")

    assert tag.id == 42
    assert tag.name == "SocialFlow"


@pytest.mark.parametrize("invalid_id", [0, -1, True, "42"])
def test_wordpress_tag_rejects_invalid_ids(invalid_id) -> None:
    with pytest.raises(ValueError, match="tag ID"):
        WordPressTag(id=invalid_id, name="Python")


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_wordpress_tag_rejects_empty_names(invalid_name) -> None:
    with pytest.raises(ValueError, match="tag name"):
        WordPressTag(id=42, name=invalid_name)