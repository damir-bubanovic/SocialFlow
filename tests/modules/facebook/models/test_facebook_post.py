
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest
from typing import Any, cast

from socialflow.modules.facebook.models.facebook_post import (
    FacebookPost,
)


CREATED_AT = datetime(
    2026, 11, 2, 10, 0, tzinfo=timezone.utc
)


def test_facebook_post_creation() -> None:
    post = FacebookPost(
        id=" 123_456 ",
        page_id=" 123 ",
        message="Hello Facebook",
        created_at=CREATED_AT,
        permalink_url="https://www.facebook.com/example",
    )

    assert post.id == "123_456"
    assert post.page_id == "123"
    assert post.message == "Hello Facebook"
    assert post.created_at == CREATED_AT
    assert post.permalink_url is not None


def test_facebook_post_allows_empty_message() -> None:
    post = FacebookPost(
        id="123_456",
        page_id="123",
        message="",
        created_at=CREATED_AT,
    )

    assert post.message == ""
    assert post.permalink_url is None


def test_facebook_post_is_immutable() -> None:
    post = FacebookPost(
        id="123_456",
        page_id="123",
        message="Original",
        created_at=CREATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(post, "message", "Changed")


@pytest.mark.parametrize("invalid_id", [
    "", " ", None, 123,
])
def test_facebook_post_rejects_invalid_id(invalid_id) -> None:
    with pytest.raises(ValueError, match="post ID"):
        FacebookPost(
            id=invalid_id,
            page_id="123",
            message="Hello",
            created_at=CREATED_AT,
        )


@pytest.mark.parametrize("invalid_page_id", [
    "", " ", None, 123,
])
def test_facebook_post_rejects_invalid_page_id(
    invalid_page_id,
) -> None:
    with pytest.raises(ValueError, match="Page ID"):
        FacebookPost(
            id="123_456",
            page_id=invalid_page_id,
            message="Hello",
            created_at=CREATED_AT,
        )


@pytest.mark.parametrize("invalid_message", [None, 123, True])
def test_facebook_post_rejects_invalid_message(
    invalid_message,
) -> None:
    with pytest.raises(ValueError, match="message"):
        FacebookPost(
            id="123_456",
            page_id="123",
            message=cast(Any, invalid_message),
            created_at=CREATED_AT,
        )


def test_facebook_post_rejects_invalid_date() -> None:
    with pytest.raises(ValueError, match="creation date"):
        FacebookPost(
            id="123_456",
            page_id="123",
            message="Hello",
            created_at=cast(Any, "2026-11-02"),
        )


def test_facebook_post_rejects_invalid_permalink() -> None:
    with pytest.raises(ValueError, match="permalink"):
        FacebookPost(
            id="123_456",
            page_id="123",
            message="Hello",
            created_at=CREATED_AT,
            permalink_url=cast(Any, 123),
        )
