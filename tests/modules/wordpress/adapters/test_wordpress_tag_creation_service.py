
"""Tests for the WordPress tag creation service adapter."""

from unittest.mock import Mock

import pytest

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.modules.posts.models.remote_tag import RemoteTag
from socialflow.modules.posts.models.tag import Tag
from socialflow.modules.posts.services.remote_tag_creation_service import (
    RemoteTagCreationService,
)
from socialflow.modules.wordpress.adapters.wordpress_tag_creation_service import (
    WordPressTagCreationService,
)
from socialflow.modules.wordpress.models.wordpress_tag import WordPressTag


def make_service():
    test_account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    credentials = Mock()
    credentials.get.return_value = "secret"

    client = Mock()

    service = WordPressTagCreationService(
        tag_client=client,
        credential_store=credentials,
    )

    return service, test_account, client


def test_adapter_implements_posts_contract():
    service, _, _ = make_service()

    assert isinstance(service, RemoteTagCreationService)


def test_preparation_detects_missing_tags():
    service, test_account, client = make_service()

    client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
    )

    missing = service.prepare_creation(
        test_account,
        (Tag("Python"), Tag("SocialFlow")),
    )

    assert missing == (Tag("SocialFlow"),)
    client.create_tag.assert_not_called()


def test_preparation_rejects_ambiguous_remote_tags():
    service, test_account, client = make_service()

    client.list_tags.return_value = (
        WordPressTag(id=101, name="Čakovec"),
        WordPressTag(id=202, name="C\u030Cakovec"),
    )

    with pytest.raises(ValueError, match="Ambiguous WordPress tag"):
        service.prepare_creation(
            test_account,
            (Tag("Čakovec"),),
        )


def test_creation_returns_remote_tags():
    service, test_account, client = make_service()

    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        WordPressTag(id=102, name="SocialFlow"),
    ]

    result = service.create_approved_tags(
        test_account,
        (Tag("Python"), Tag("SocialFlow")),
    )

    assert result == (
        RemoteTag(remote_id=101, name="Python"),
        RemoteTag(remote_id=102, name="SocialFlow"),
    )
    assert client.create_tag.call_count == 2


def test_creation_stops_after_first_failure():
    service, test_account, client = make_service()

    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        RuntimeError("WordPress API unavailable."),
    ]

    with pytest.raises(RuntimeError, match="WordPress API unavailable"):
        service.create_approved_tags(
            test_account,
            (Tag("Python"), Tag("SocialFlow"), Tag("Linux")),
        )

    assert client.create_tag.call_count == 2


def test_creation_rejects_invalid_result():
    service, test_account, client = make_service()
    client.create_tag.return_value = None

    with pytest.raises(ValueError, match="Invalid WordPress tag"):
        service.create_approved_tags(
            test_account,
            (Tag("Python"),),
        )


def test_creation_accepts_unicode_equivalent_name():
    service, test_account, client = make_service()

    client.create_tag.return_value = WordPressTag(
        id=101,
        name="C\u030Cakovec",
    )

    result = service.create_approved_tags(
        test_account,
        (Tag("Čakovec"),),
    )

    assert result == (
        RemoteTag(remote_id=101, name="C\u030Cakovec"),
    )


def test_creation_rejects_different_name():
    service, test_account, client = make_service()

    client.create_tag.return_value = WordPressTag(
        id=101,
        name="WrongTag",
    )

    with pytest.raises(ValueError, match="Invalid WordPress tag"):
        service.create_approved_tags(
            test_account,
            (Tag("SocialFlow"),),
        )
