from dataclasses import FrozenInstanceError

import pytest

from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)


def test_wordpress_configuration_is_complete() -> None:
    config = WordPressConnectionConfig(
        site_url="https://example.com",
        username="admin",
    )

    assert config.is_complete() is True


@pytest.mark.parametrize(
    ("site_url", "username"),
    [
        ("", "admin"),
        ("https://example.com", ""),
        ("   ", "admin"),
        ("https://example.com", "   "),
    ],
)
def test_wordpress_configuration_requires_both_fields(
    site_url: str,
    username: str,
) -> None:
    config = WordPressConnectionConfig(
        site_url=site_url,
        username=username,
    )

    assert config.is_complete() is False


def test_wordpress_configuration_normalizes_values() -> None:
    config = WordPressConnectionConfig(
        site_url="  https://example.com/  ",
        username="  admin  ",
    )

    normalized = config.normalized()

    assert normalized.site_url == "https://example.com"
    assert normalized.username == "admin"


def test_wordpress_configuration_is_immutable() -> None:
    config = WordPressConnectionConfig(
        site_url="https://example.com",
        username="admin",
    )

    with pytest.raises(FrozenInstanceError):
        setattr(config, "username", "other")