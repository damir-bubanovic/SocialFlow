
from dataclasses import FrozenInstanceError

import pytest

from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


def test_facebook_page_normalizes_values() -> None:
    page = FacebookPage(
        id=" 123456789 ",
        name=" My Test Page ",
    )

    assert page.id == "123456789"
    assert page.name == "My Test Page"


def test_facebook_page_is_immutable() -> None:
    page = FacebookPage(id="123", name="Test")

    with pytest.raises(FrozenInstanceError):
        setattr(page, "name", "Changed")


@pytest.mark.parametrize("invalid_id", [
    "", "   ", None, 123, True,
])
def test_facebook_page_rejects_invalid_id(invalid_id) -> None:
    with pytest.raises(ValueError, match="Page ID"):
        FacebookPage(id=invalid_id, name="Test")


@pytest.mark.parametrize("invalid_name", [
    "", "   ", None, 123,
])
def test_facebook_page_rejects_invalid_name(invalid_name) -> None:
    with pytest.raises(ValueError, match="Page name"):
        FacebookPage(id="123", name=invalid_name)
