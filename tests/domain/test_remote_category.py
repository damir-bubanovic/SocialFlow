from dataclasses import FrozenInstanceError

import pytest

from socialflow.domain.post.remote_category import RemoteCategory


def test_remote_category_stores_top_level_category():
    category = RemoteCategory(
        remote_id=12,
        name="  Technology  ",
    )

    assert category.remote_id == 12
    assert category.name == "Technology"
    assert category.parent_id == 0


def test_remote_category_stores_subcategory():
    category = RemoteCategory(
        remote_id=34,
        name="Python",
        parent_id=12,
    )

    assert category.remote_id == 34
    assert category.name == "Python"
    assert category.parent_id == 12


def test_remote_category_is_immutable():
    category = RemoteCategory(
        remote_id=12,
        name="Technology",
    )

    with pytest.raises(FrozenInstanceError):
        setattr(category, "name", "News")

    assert category.name == "Technology"


@pytest.mark.parametrize(
    "remote_id",
    [0, -1, True, False, "12", 12.5, None],
)
def test_remote_category_rejects_invalid_ids(remote_id):
    with pytest.raises(
        ValueError,
        match="Remote category ID must be a positive integer",
    ):
        RemoteCategory(
            remote_id=remote_id,
            name="Technology",
        )


@pytest.mark.parametrize(
    "name",
    ["", "   ", "\t", None, 123],
)
def test_remote_category_rejects_invalid_names(name):
    with pytest.raises(
        ValueError,
        match="Remote category name must be a non-empty string|"
              "Remote category name cannot be empty",
    ):
        RemoteCategory(
            remote_id=12,
            name=name,
        )


@pytest.mark.parametrize(
    "parent_id",
    [-1, True, False, "12", 12.5, None],
)
def test_remote_category_rejects_invalid_parent_ids(parent_id):
    with pytest.raises(
        ValueError,
        match="Parent category ID must be a non-negative integer",
    ):
        RemoteCategory(
            remote_id=12,
            name="Python",
            parent_id=parent_id,
        )


def test_remote_category_cannot_be_its_own_parent():
    with pytest.raises(
        ValueError,
        match="A category cannot be its own parent",
    ):
        RemoteCategory(
            remote_id=12,
            name="Python",
            parent_id=12,
        )