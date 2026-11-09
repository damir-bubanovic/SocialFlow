
from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


def make_page(token: str = "secret-token") -> DiscoveredFacebookPage:
    return DiscoveredFacebookPage(
        page=FacebookPage(id="123", name="Test Page"),
        access_token=token,
    )


def test_discovered_page_contains_page_identity() -> None:
    discovered = make_page()

    assert discovered.page.id == "123"
    assert discovered.page.name == "Test Page"
    assert discovered.access_token == "secret-token"


def test_discovered_page_normalizes_token() -> None:
    discovered = make_page("  secret-token  ")

    assert discovered.access_token == "secret-token"


def test_discovered_page_repr_hides_token() -> None:
    discovered = make_page()

    representation = repr(discovered)

    assert "secret-token" not in representation
    assert "Test Page" in representation


def test_discovered_page_equality_excludes_token() -> None:
    first = make_page("token-one")
    second = make_page("token-two")

    assert first == second


def test_discovered_page_is_immutable() -> None:
    discovered = make_page()

    with pytest.raises(FrozenInstanceError):
        setattr(discovered, "access_token", "changed")


@pytest.mark.parametrize(
    "invalid_token",
    ["", " ", "\t", None, 123, True],
)
def test_discovered_page_rejects_invalid_token(
    invalid_token: Any,
) -> None:
    with pytest.raises(ValueError, match="access token"):
        DiscoveredFacebookPage(
            page=FacebookPage(id="123", name="Test"),
            access_token=cast(Any, invalid_token),
        )


@pytest.mark.parametrize(
    "invalid_page",
    [None, "page", 123],
)
def test_discovered_page_rejects_invalid_page(
    invalid_page: Any,
) -> None:
    with pytest.raises(ValueError, match="Page"):
        DiscoveredFacebookPage(
            page=cast(Any, invalid_page),
            access_token="token",
        )
