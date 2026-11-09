
from typing import Any, cast

import pytest

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_page_parser import (
    parse_discovered_pages,
)


def test_parse_one_page() -> None:
    pages = parse_discovered_pages(
        {
            "data": [
                {
                    "id": "123",
                    "name": "Test Page",
                    "access_token": "page-token",
                }
            ]
        }
    )

    assert len(pages) == 1
    assert pages[0].page.id == "123"
    assert pages[0].page.name == "Test Page"
    assert pages[0].access_token == "page-token"


def test_parse_multiple_pages() -> None:
    pages = parse_discovered_pages(
        {
            "data": [
                {
                    "id": "123",
                    "name": "First",
                    "access_token": "token-one",
                },
                {
                    "id": "456",
                    "name": "Second",
                    "access_token": "token-two",
                },
            ]
        }
    )

    assert [page.page.id for page in pages] == ["123", "456"]


def test_parse_empty_page_list() -> None:
    assert parse_discovered_pages({"data": []}) == []


def test_parser_normalizes_values() -> None:
    pages = parse_discovered_pages(
        {
            "data": [
                {
                    "id": " 123 ",
                    "name": " My Page ",
                    "access_token": " secret ",
                }
            ]
        }
    )

    assert pages[0].page.id == "123"
    assert pages[0].page.name == "My Page"
    assert pages[0].access_token == "secret"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "invalid",
        123,
        {},
        {"data": None},
        {"data": {}},
        {"data": "invalid"},
    ],
)
def test_parser_rejects_invalid_response(
    payload: Any,
) -> None:
    with pytest.raises(FacebookApiError):
        parse_discovered_pages(cast(Any, payload))


@pytest.mark.parametrize(
    "entry",
    [
        None,
        "invalid",
        123,
        [],
        {},
        {"id": "123"},
        {"id": "123", "name": "Page"},
        {"id": "123", "access_token": "token"},
        {"name": "Page", "access_token": "token"},
        {"id": "", "name": "Page", "access_token": "token"},
        {"id": " ", "name": "Page", "access_token": "token"},
        {"id": 123, "name": "Page", "access_token": "token"},
        {"id": "123", "name": "", "access_token": "token"},
        {"id": "123", "name": 123, "access_token": "token"},
        {"id": "123", "name": "Page", "access_token": ""},
        {"id": "123", "name": "Page", "access_token": None},
        {"id": "123", "name": "Page", "access_token": 123},
    ],
)
def test_parser_rejects_invalid_entry(
    entry: Any,
) -> None:
    with pytest.raises(FacebookApiError):
        parse_discovered_pages({"data": [entry]})


def test_parser_rejects_duplicate_page_ids() -> None:
    payload = {
        "data": [
            {
                "id": "123",
                "name": "First",
                "access_token": "token-one",
            },
            {
                "id": " 123 ",
                "name": "Second",
                "access_token": "token-two",
            },
        ]
    }

    with pytest.raises(FacebookApiError):
        parse_discovered_pages(payload)


def test_parser_does_not_expose_tokens_in_errors() -> None:
    payload = {
        "data": [
            {
                "id": "123",
                "name": "Page",
                "access_token": "secret-token",
            },
            {
                "id": "123",
                "name": "Duplicate",
                "access_token": "another-secret",
            },
        ]
    }

    with pytest.raises(FacebookApiError) as exc_info:
        parse_discovered_pages(payload)

    error = exc_info.value

    assert "secret-token" not in str(error)
    assert "another-secret" not in str(error)
    assert "secret-token" not in error.message


def test_parser_does_not_modify_input() -> None:
    entry = {
        "id": " 123 ",
        "name": " Page ",
        "access_token": " token ",
    }
    payload = {"data": [entry]}

    parse_discovered_pages(payload)

    assert entry["id"] == " 123 "
    assert entry["name"] == " Page "
    assert entry["access_token"] == " token "
