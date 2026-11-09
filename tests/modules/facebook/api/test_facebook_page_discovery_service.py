
import json
from typing import Any, Mapping, cast
from urllib.error import URLError

import pytest

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.api.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)


class DiscoveryTransport(FacebookHttpTransport):
    def __init__(
        self,
        payload: Any = None,
        status: int = 200,
        failure: Exception | None = None,
    ) -> None:
        if payload is None:
            payload = {
                "data": [
                    {
                        "id": "123",
                        "name": "My Page",
                        "access_token": "page-secret",
                    }
                ]
            }

        self.payload = payload
        self.status = status
        self.failure = failure
        self.requests: list[
            tuple[str, dict[str, str], float]
        ] = []

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        self.requests.append(
            (url, dict(headers), timeout)
        )

        if self.failure is not None:
            raise self.failure

        return FacebookHttpResponse(
            status_code=self.status,
            body=json.dumps(self.payload).encode("utf-8"),
        )

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> FacebookHttpResponse:
        raise NotImplementedError(
            "POST is not supported by this test transport."
        )


def make_service(
    transport: DiscoveryTransport,
    limit: int = 25,
) -> FacebookPageDiscoveryService:
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
    )
    return FacebookPageDiscoveryService(
        client,
        limit=limit,
    )


def test_discovery_returns_page_and_token() -> None:
    transport = DiscoveryTransport()
    service = make_service(transport)

    pages = service.discover("user-secret")

    assert len(pages) == 1
    assert pages[0].page.id == "123"
    assert pages[0].page.name == "My Page"
    assert pages[0].access_token == "page-secret"


def test_discovery_requests_correct_endpoint() -> None:
    transport = DiscoveryTransport()
    service = make_service(transport)

    service.discover("user-secret")

    url, headers, _ = transport.requests[0]

    assert url.startswith(
        "https://graph.facebook.com/v24.0/me/accounts?"
    )
    assert "fields=id%2Cname%2Caccess_token" in url
    assert "limit=25" in url
    assert headers["Authorization"] == "Bearer user-secret"
    assert "user-secret" not in url


def test_discovery_uses_custom_limit() -> None:
    transport = DiscoveryTransport()
    service = make_service(transport, limit=5)

    service.discover("user-secret")

    assert "limit=5" in transport.requests[0][0]


def test_discovery_normalizes_user_token() -> None:
    transport = DiscoveryTransport()
    service = make_service(transport)

    service.discover("  user-secret  ")

    assert transport.requests[0][1]["Authorization"] == (
        "Bearer user-secret"
    )


def test_discovery_returns_empty_list() -> None:
    transport = DiscoveryTransport(payload={"data": []})
    service = make_service(transport)

    assert service.discover("user-secret") == []


def test_discovery_returns_multiple_pages() -> None:
    transport = DiscoveryTransport(
        payload={
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
    service = make_service(transport)

    pages = service.discover("user-secret")

    assert [page.page.id for page in pages] == [
        "123",
        "456",
    ]


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        101,
        True,
        False,
        1.5,
        "25",
        None,
    ],
)
def test_discovery_rejects_invalid_limit(
    limit: Any,
) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=DiscoveryTransport(),
    )

    with pytest.raises(ValueError, match="limit"):
        FacebookPageDiscoveryService(
            client,
            limit=cast(Any, limit),
        )


@pytest.mark.parametrize(
    "token",
    [
        "",
        " ",
        "\t",
        None,
        123,
        True,
    ],
)
def test_discovery_rejects_invalid_user_token(
    token: Any,
) -> None:
    transport = DiscoveryTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="token"):
        service.discover(cast(Any, token))

    assert transport.requests == []


@pytest.mark.parametrize(
    "client",
    [
        None,
        "invalid",
        123,
    ],
)
def test_discovery_rejects_invalid_client(
    client: Any,
) -> None:
    with pytest.raises(ValueError, match="client"):
        FacebookPageDiscoveryService(
            cast(Any, client),
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"data": None},
        {"data": "invalid"},
        {"data": [None]},
        {"data": [{"id": "123"}]},
    ],
)
def test_discovery_rejects_malformed_page_response(
    payload: Any,
) -> None:
    transport = DiscoveryTransport(payload=payload)
    service = make_service(transport)

    with pytest.raises(FacebookApiError):
        service.discover("user-secret")


def test_discovery_rejects_more_pages_than_limit() -> None:
    transport = DiscoveryTransport(
        payload={
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
    service = make_service(transport, limit=1)

    with pytest.raises(FacebookApiError):
        service.discover("user-secret")


def test_discovery_preserves_api_error() -> None:
    transport = DiscoveryTransport(
        payload={
            "error": {
                "message": "Sensitive diagnostic",
                "type": "OAuthException",
                "code": 190,
            }
        },
        status=401,
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover("user-secret")

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == 190
    assert "Sensitive diagnostic" not in str(exc_info.value)


def test_discovery_handles_network_failure() -> None:
    transport = DiscoveryTransport(
        failure=URLError("user-secret")
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover("user-secret")

    assert exc_info.value.is_transient is True
    assert "user-secret" not in str(exc_info.value)


def test_discovery_does_not_expose_page_token_in_repr() -> None:
    service = make_service(DiscoveryTransport())

    pages = service.discover("user-secret")

    assert "page-secret" not in repr(pages)


def test_discovery_does_not_follow_pagination() -> None:
    transport = DiscoveryTransport(
        payload={
            "data": [
                {
                    "id": "123",
                    "name": "My Page",
                    "access_token": "page-secret",
                }
            ],
            "paging": {
                "next": (
                    "https://graph.facebook.com/"
                    "v24.0/me/accounts?after=cursor"
                )
            },
        }
    )
    service = make_service(transport)

    pages = service.discover("user-secret")

    assert len(pages) == 1
    assert len(transport.requests) == 1



def test_discovery_rejects_duplicate_pages_without_leaking_tokens() -> None:
    transport = DiscoveryTransport(
        payload={
            "data": [
                {
                    "id": "123",
                    "name": "First",
                    "access_token": "page-secret-one",
                },
                {
                    "id": "123",
                    "name": "Second",
                    "access_token": "page-secret-two",
                },
            ]
        }
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover("user-secret")

    error = exc_info.value

    assert "page-secret-one" not in str(error)
    assert "page-secret-two" not in str(error)
    assert "user-secret" not in str(error)
    assert len(transport.requests) == 1


def test_discovery_rejects_oversized_response_without_leaking_tokens() -> None:
    transport = DiscoveryTransport(
        payload={
            "data": [
                {
                    "id": str(index),
                    "name": f"Page {index}",
                    "access_token": f"page-secret-{index}",
                }
                for index in range(3)
            ]
        }
    )
    service = make_service(transport, limit=2)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover("user-secret")

    assert "page-secret" not in str(exc_info.value)
    assert "user-secret" not in str(exc_info.value)
    assert len(transport.requests) == 1


def test_discovery_preserves_page_order() -> None:
    transport = DiscoveryTransport(
        payload={
            "data": [
                {
                    "id": "300",
                    "name": "Third",
                    "access_token": "token-three",
                },
                {
                    "id": "100",
                    "name": "First",
                    "access_token": "token-one",
                },
                {
                    "id": "200",
                    "name": "Second",
                    "access_token": "token-two",
                },
            ]
        }
    )
    service = make_service(transport)

    pages = service.discover("user-secret")

    assert [page.page.id for page in pages] == [
        "300",
        "100",
        "200",
    ]
    assert len(transport.requests) == 1


def test_discovery_does_not_mutate_response_payload() -> None:
    payload = {
        "data": [
            {
                "id": " 123 ",
                "name": " My Page ",
                "access_token": " page-secret ",
            }
        ]
    }
    transport = DiscoveryTransport(payload=payload)
    service = make_service(transport)

    pages = service.discover("user-secret")

    assert pages[0].page.id == "123"
    assert pages[0].page.name == "My Page"
    assert pages[0].access_token == "page-secret"

    assert payload["data"][0]["id"] == " 123 "
    assert payload["data"][0]["name"] == " My Page "
    assert payload["data"][0]["access_token"] == " page-secret "
