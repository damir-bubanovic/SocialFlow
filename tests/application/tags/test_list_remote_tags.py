
from unittest.mock import Mock

from socialflow.application.tags.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.application.tags.remote_tag_provider import (
    RemoteTagProvider,
)
from socialflow.domain.post.remote_tag import RemoteTag


def test_list_remote_tags_returns_provider_results():
    account = Mock()
    expected = (
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    )

    provider = Mock(spec=RemoteTagProvider)
    provider.list_remote_tags.return_value = expected

    use_case = ListRemoteTags(provider)

    assert use_case.execute(account) == expected
    provider.list_remote_tags.assert_called_once_with(account)


def test_list_remote_tags_returns_empty_tuple():
    account = Mock()
    provider = Mock(spec=RemoteTagProvider)
    provider.list_remote_tags.return_value = ()

    use_case = ListRemoteTags(provider)

    assert use_case.execute(account) == ()
    provider.list_remote_tags.assert_called_once_with(account)
