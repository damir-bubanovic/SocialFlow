
from dataclasses import FrozenInstanceError

import pytest

from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)


def test_top_level_category():
    category = WordPressCategory(id=10, name=" Technology ")

    assert category.id == 10
    assert category.name == "Technology"
    assert category.parent_id == 0


def test_subcategory():
    category = WordPressCategory(
        id=20,
        name="Python",
        parent_id=10,
    )

    assert category.parent_id == 10


def test_category_is_immutable():
    category = WordPressCategory(id=10, name="Technology")

    with pytest.raises(FrozenInstanceError):
        setattr(category, "name", "News")


@pytest.mark.parametrize("invalid_id", [0, -1, True, "10", None])
def test_invalid_category_id(invalid_id):
    with pytest.raises(ValueError, match="category ID"):
        WordPressCategory(id=invalid_id, name="Technology")


@pytest.mark.parametrize("invalid_name", ["", "  ", None, 123])
def test_invalid_category_name(invalid_name):
    with pytest.raises(ValueError, match="category name"):
        WordPressCategory(id=10, name=invalid_name)


@pytest.mark.parametrize("invalid_parent", [-1, True, "10", None])
def test_invalid_parent_id(invalid_parent):
    with pytest.raises(ValueError, match="parent category ID"):
        WordPressCategory(
            id=10,
            name="Python",
            parent_id=invalid_parent,
        )


def test_category_cannot_be_its_own_parent():
    with pytest.raises(ValueError, match="own parent"):
        WordPressCategory(
            id=10,
            name="Python",
            parent_id=10,
        )
