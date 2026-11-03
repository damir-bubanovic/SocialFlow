
import json
from typing import Any, Mapping
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

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


USER_TOKEN = "user-secret-123"
PAGE_TOKEN = "page-secret-456"


class RecordingTransport(FacebookHttpTransport):
    """Simulate Graph API HTTP responses without network access."""

    def __init__(
        self,
        status: int = 200,
        body: bytes = b'{"data":[]}',
        failure: Exception | None = None,
    ) -> None:
        self.status = status
        self.body = body
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
            body=self.body,
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


def make_transport(
    payload: dict[str, Any],
    status: int = 200,
) -> RecordingTransport:
    return RecordingTransport(
        status=status,
        body=json.dumps(payload).encode("utf-8"),
    )


def make_service(
    transport: RecordingTransport,
    limit: int = 25,
) -> FacebookPageDiscoveryService:
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )
    return FacebookPageDiscoveryService(
        client,
        limit=limit,
    )


def page_payload(
    page_id: str = "123",
    token: str = PAGE_TOKEN,
) -> dict[str, Any]:
    return {
        "data": [
            {
                "id": page_id,
                "name": "Integration Page",
                "access_token": token,
            }
        ]
    }


def test_complete_discovery_pipeline() -> None:
    transport = make_transport(page_payload())
    service = make_service(transport)

    pages = service.discover(USER_TOKEN)

    assert len(pages) == 1
    assert pages[0].page.id == "123"
    assert pages[0].page.name == "Integration Page"
    assert pages[0].access_token == PAGE_TOKEN
    assert len(transport.requests) == 1


def test_request_uses_correct_endpoint_and_parameters() -> None:
    transport = make_transport(page_payload())
    service = make_service(transport, limit=10)

    service.discover(USER_TOKEN)

    url, headers, timeout = transport.requests[0]
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.hostname == "graph.facebook.com"
    assert parsed.path == "/v24.0/me/accounts"
    assert query == {
        "fields": ["id,name,access_token"],
        "limit": ["10"],
    }
    assert headers["Authorization"] == f"Bearer {USER_TOKEN}"
    assert headers["Accept"] == "application/json"
    assert timeout == 7.5


def test_credentials_are_absent_from_request_url() -> None:
    transport = make_transport(page_payload())
    service = make_service(transport)

    service.discover(USER_TOKEN)

    url, _, _ = transport.requests[0]

    assert USER_TOKEN not in url
    assert PAGE_TOKEN not in url
    assert "access_token=" not in url


def test_discovery_preserves_page_order() -> None:
    transport = make_transport(
        {
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
            ]
        }
    )

    pages = make_service(transport).discover(USER_TOKEN)

    assert [page.page.id for page in pages] == [
        "300",
        "100",
    ]


@pytest.mark.parametrize(
    "status,code,transient",
    [
        (401, 190, False),
        (403, 200, False),
        (429, 4, True),
        (500, 1, True),
        (503, 2, True),
    ],
)
def test_graph_api_errors_propagate_safely(
    status: int,
    code: int,
    transient: bool,
) -> None:
    transport = make_transport(
        {
            "error": {
                "message": f"Sensitive {USER_TOKEN}",
                "type": "OAuthException",
                "code": code,
            }
        },
        status=status,
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover(USER_TOKEN)

    error = exc_info.value

    assert error.status_code == status
    assert error.code == code
    assert error.is_transient is transient
    assert USER_TOKEN not in str(error)
    assert USER_TOKEN not in repr(error)
    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError(USER_TOKEN),
        URLError(USER_TOKEN),
        OSError(USER_TOKEN),
    ],
)
def test_transport_failures_are_sanitized(
    failure: Exception,
) -> None:
    transport = RecordingTransport(failure=failure)
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover(USER_TOKEN)

    error = exc_info.value

    assert error.is_transient is True
    assert USER_TOKEN not in str(error)
    assert USER_TOKEN not in repr(error)
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"not-json",
        b"[]",
        b"null",
        b'{"data":null}',
        b'{"data":[{"id":"123"}]}',
    ],
)
def test_malformed_responses_are_rejected(
    body: bytes,
) -> None:
    transport = RecordingTransport(body=body)
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.discover(USER_TOKEN)

    assert USER_TOKEN not in str(exc_info.value)
    assert PAGE_TOKEN not in str(exc_info.value)
    assert len(transport.requests) == 1


def test_duplicate_page_ids_are_rejected() -> None:
    transport = make_transport(
        {
            "data": [
                {
                    "id": "123",
                    "name": "First",
                    "access_token": PAGE_TOKEN,
                },
                {
                    "id": " 123 ",
                    "name": "Second",
                    "access_token": "other-page-secret",
                },
            ]
        }
    )

    with pytest.raises(FacebookApiError) as exc_info:
        make_service(transport).discover(USER_TOKEN)

    assert PAGE_TOKEN not in str(exc_info.value)
    assert USER_TOKEN not in str(exc_info.value)


def test_oversized_response_is_rejected() -> None:
    transport = make_transport(
        {
            "data": [
                {
                    "id": str(index),
                    "name": f"Page {index}",
                    "access_token": f"token-{index}",
                }
                for index in range(3)
            ]
        }
    )

    service = make_service(transport, limit=2)

    with pytest.raises(FacebookApiError):
        service.discover(USER_TOKEN)

    assert len(transport.requests) == 1


def test_pagination_is_not_followed_automatically() -> None:
    transport = make_transport(
        {
            **page_payload(),
            "paging": {
                "next": (
                    "https://graph.facebook.com/"
                    "v24.0/me/accounts?after=cursor"
                )
            },
        }
    )

    pages = make_service(transport).discover(USER_TOKEN)

    assert len(pages) == 1
    assert len(transport.requests) == 1


def test_empty_discovery_is_valid() -> None:
    transport = make_transport({"data": []})

    pages = make_service(transport).discover(USER_TOKEN)

    assert pages == []
    assert len(transport.requests) == 1
