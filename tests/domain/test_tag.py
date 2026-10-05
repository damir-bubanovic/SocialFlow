import pytest

from socialflow.domain.post.tag import Tag


def test_tag_contains_name() -> None:
    tag = Tag(name="SocialFlow")

    assert tag.name == "SocialFlow"


def test_tag_strips_surrounding_whitespace() -> None:
    tag = Tag(name="  SocialFlow  ")

    assert tag.name == "SocialFlow"


def test_tag_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Tag name cannot be empty.",
    ):
        Tag(name="")


def test_tag_rejects_whitespace_only_name() -> None:
    with pytest.raises(
        ValueError,
        match="Tag name cannot be empty.",
    ):
        Tag(name="   ")