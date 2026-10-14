import pytest

from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)


def test_wordpress_tag_client_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        WordPressTagClient()


def test_wordpress_tag_client_requires_list_tags() -> None:
    with pytest.raises(TypeError):
        WordPressTagClient()


def test_wordpress_tag_client_supports_concrete_implementations() -> None:
    class FakeClient(WordPressTagClient):
        def list_tags(
            self,
            site_url: str,
            username: str,
            application_password: str,
        ) -> tuple[WordPressTag, ...]:
            return (WordPressTag(id=12, name="Python"),)

        def create_tag(
            self,
            site_url: str,
            username: str,
            application_password: str,
            name: str,
        ) -> WordPressTag:
            return WordPressTag(id=42, name=name)

    client = FakeClient()

    assert client.list_tags(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
    ) == (WordPressTag(id=12, name="Python"),)