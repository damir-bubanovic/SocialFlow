
import pytest

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)


def test_error_repr_does_not_expose_message() -> None:
    error = FacebookApiError(
        message="Sensitive token: user-secret-123",
        status_code=401,
        code=190,
    )

    representation = repr(error)

    assert "user-secret-123" not in representation
    assert "Sensitive token" not in representation
    assert "401" in representation
    assert "190" in representation


def test_error_repr_does_not_expose_error_type() -> None:
    error = FacebookApiError(
        message="Facebook request failed.",
        error_type="secret-type-value",
    )

    assert "secret-type-value" not in repr(error)


def test_error_string_does_not_expose_message() -> None:
    error = FacebookApiError(
        message="Sensitive token: user-secret-123",
        status_code=403,
        code=200,
    )

    text = str(error)

    assert "user-secret-123" not in text
    assert "403" in text
    assert "200" in text


def test_error_preserves_structured_fields() -> None:
    error = FacebookApiError(
        message="Facebook request failed.",
        status_code=429,
        code=4,
        subcode=123,
        is_transient=True,
        error_type="OAuthException",
    )

    assert error.message == "Facebook request failed."
    assert error.status_code == 429
    assert error.code == 4
    assert error.subcode == 123
    assert error.is_transient is True
    assert error.error_type == "OAuthException"


def test_error_remains_an_exception() -> None:
    error = FacebookApiError(
        message="Facebook request failed.",
        status_code=500,
    )

    with pytest.raises(FacebookApiError) as exc_info:
        raise error

    assert exc_info.value.status_code == 500


def test_error_repr_does_not_expose_page_token() -> None:
    error = FacebookApiError(
        message="Page token: page-secret-456",
        error_type="page-secret-456",
    )

    assert "page-secret-456" not in repr(error)
    assert "page-secret-456" not in str(error)
