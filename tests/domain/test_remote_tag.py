import pytest
from dataclasses import FrozenInstanceError

from socialflow.domain.post.remote_tag import RemoteTag


def test_remote_tag_stores_id_and_normalized_name():
    tag = RemoteTag(remote_id=12, name="  Technology  ")

    assert tag.remote_id == 12
    assert tag.name == "Technology"


def test_remote_tag_is_immutable():
    tag = RemoteTag(remote_id=12, name="Technology")

    with pytest.raises(FrozenInstanceError):
        setattr(tag, "name", "News")


@pytest.mark.parametrize(
    "remote_id",
    [0, -1, True, False, "12", 12.5, None],
)
def test_remote_tag_rejects_invalid_ids(remote_id):
    with pytest.raises(
        ValueError,
        match="Remote tag ID must be a positive integer",
    ):
        RemoteTag(remote_id=remote_id, name="Technology")


@pytest.mark.parametrize(
    "name",
    ["", "   ", "\t"],
)
def test_remote_tag_rejects_empty_names(name):
    with pytest.raises(
        ValueError,
        match="Remote tag name cannot be empty",
    ):
        RemoteTag(remote_id=12, name=name)
