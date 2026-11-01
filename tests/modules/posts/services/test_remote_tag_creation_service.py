
"""Tests for the remote tag creation service contract."""

import inspect
from unittest.mock import Mock

import pytest

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag
from socialflow.modules.posts.services.remote_tag_creation_service import (
    RemoteTagCreationService,
)
from socialflow.modules.posts.models.remote_tag import RemoteTag


def test_remote_tag_creation_service_is_abstract() -> None:
    """The base contract must be abstract."""
    assert inspect.isabstract(RemoteTagCreationService)

    assert RemoteTagCreationService.__abstractmethods__ == {
        "prepare_creation",
        "create_approved_tags",
    }


def test_remote_tag_creation_service_requires_both_operations() -> None:
    """Both workflow operations must be implemented."""

    class IncompleteService(RemoteTagCreationService):
        def prepare_creation(
            self,
            target_account: Account,
            requested_tags: tuple[Tag, ...],
        ) -> tuple[Tag, ...]:
            return ()

        def create_approved_tags(
            self,
            target_account: Account,
            approved_tags: tuple[Tag, ...],
        ) -> tuple[RemoteTag, ...]:
            raise NotImplementedError

    assert not inspect.isabstract(IncompleteService)

    service = IncompleteService()

    with pytest.raises(NotImplementedError):
        service.create_approved_tags(Mock(spec=Account), ())


def test_remote_tag_creation_service_can_be_implemented() -> None:
    """A concrete implementation can satisfy the contract."""

    class FakeService(RemoteTagCreationService):
        def prepare_creation(
            self,
            target_account: Account,
            requested_tags: tuple[Tag, ...],
        ) -> tuple[Tag, ...]:
            return requested_tags

        def create_approved_tags(
            self,
            target_account: Account,
            approved_tags: tuple[Tag, ...],
        ) -> tuple[RemoteTag, ...]:
            return tuple(
                RemoteTag(remote_id=index, name=tag.name)
                for index, tag in enumerate(approved_tags, start=1)
            )

    test_account = Mock(spec=Account)
    service = FakeService()

    test_tags = (
        Tag("Python"),
        Tag("SocialFlow"),
    )

    assert service.prepare_creation(test_account, test_tags) == test_tags
    assert service.create_approved_tags(test_account, test_tags) == (
        RemoteTag(remote_id=1, name="Python"),
        RemoteTag(remote_id=2, name="SocialFlow"),
    )
