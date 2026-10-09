from dataclasses import FrozenInstanceError

import pytest

from socialflow.infrastructure.wordpress.wordpress_http_client import (
    WordPressHttpClient,
    WordPressHttpResponse,
)


def test_http_response_stores_status_code() -> None:
    response = WordPressHttpResponse(status_code=200)

    assert response.status_code == 200


def test_http_response_is_immutable() -> None:
    response = WordPressHttpResponse(status_code=200)

    with pytest.raises(FrozenInstanceError):
        setattr(response, "status_code", 401)


def test_http_client_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        WordPressHttpClient()