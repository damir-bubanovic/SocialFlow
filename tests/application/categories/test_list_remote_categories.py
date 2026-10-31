from unittest.mock import Mock

from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.application.categories.remote_category_provider import (
    RemoteCategoryProvider,
)
from socialflow.domain.post.remote_category import RemoteCategory


def test_list_remote_categories_returns_provider_results():
    account = Mock()

    expected = (
        RemoteCategory(remote_id=12, name="Technology"),
        RemoteCategory(
            remote_id=34,
            name="Python",
            parent_id=12,
        ),
    )

    provider = Mock(spec=RemoteCategoryProvider)
    provider.list_remote_categories.return_value = expected

    use_case = ListRemoteCategories(provider)

    assert use_case.execute(account) == expected
    provider.list_remote_categories.assert_called_once_with(account)


def test_list_remote_categories_returns_empty_tuple():
    account = Mock()

    provider = Mock(spec=RemoteCategoryProvider)
    provider.list_remote_categories.return_value = ()

    use_case = ListRemoteCategories(provider)

    assert use_case.execute(account) == ()
    provider.list_remote_categories.assert_called_once_with(account)