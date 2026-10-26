from unittest.mock import Mock

import pytest

from socialflow.application.publishing.update_remote_post import (
    UpdateRemotePost,
)


def test_update_remote_post_delegates_to_updater():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )


def test_update_remote_post_propagates_updater_errors():
    updater = Mock()
    updater.update_post.side_effect = RuntimeError(
        "WordPress post update failed (HTTP 403)."
    )

    use_case = UpdateRemotePost(updater=updater)

    with pytest.raises(
        RuntimeError,
        match="WordPress post update failed",
    ):
        use_case.execute(
            account=Mock(),
            post_id=123,
            content="Updated content",
        )

    updater.update_post.assert_called_once()


def test_update_remote_post_forwards_tag_ids():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )


def test_update_remote_post_forwards_empty_tags():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(),
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(),
    )


def test_update_remote_post_forwards_featured_media_id():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )


def test_update_remote_post_forwards_featured_media_removal():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=0,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=0,
    )


def test_update_remote_post_forwards_tags_and_featured_media():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=456,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=456,
    )

@pytest.mark.parametrize(
    "status",
    ("draft", "pending", "private", "publish"),
)
def test_update_remote_post_forwards_status(status):
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        status=status,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        status=status,
    )



def test_update_remote_post_replaces_featured_image_without_changing_other_metadata():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Existing content čćžšđ",
        featured_media_id=789,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Existing content čćžšđ",
        featured_media_id=789,
    )

    update_kwargs = updater.update_post.call_args.kwargs

    assert "tags" not in update_kwargs
    assert "status" not in update_kwargs



@pytest.mark.parametrize(
    "featured_media_id",
    [456, 0],
    ids=["replace-image", "remove-image"],
)
def test_featured_image_update_preserves_unspecified_metadata(
    featured_media_id,
):
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Existing content čćžšđ",
        featured_media_id=featured_media_id,
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Existing content čćžšđ",
        featured_media_id=featured_media_id,
    )

    kwargs = updater.update_post.call_args.kwargs
    assert "tags" not in kwargs
    assert "status" not in kwargs


def test_featured_image_update_can_include_explicit_tags_and_status():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=789,
        status="draft",
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=789,
        status="draft",
    )


def test_omitted_featured_image_does_not_modify_remote_media():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)

    use_case.execute(
        account=Mock(),
        post_id=123,
        content="Updated content",
        tags=(),
    )

    kwargs = updater.update_post.call_args.kwargs

    assert kwargs["tags"] == ()
    assert "featured_media_id" not in kwargs
