
import pytest
from typing import Any, cast

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)


def test_facebook_api_error_contains_structured_fields() -> None:
    error = FacebookApiError(
        message="Permission denied",
        status_code=403,
        code=200,
        subcode=10,
        error_type="OAuthException",
    )

    assert error.status_code == 403
    assert error.code == 200
    assert error.subcode == 10
    assert error.error_type == "OAuthException"
    assert error.is_transient is False


def test_facebook_api_error_is_exception() -> None:
    with pytest.raises(FacebookApiError):
        raise FacebookApiError(
            message="Request failed",
            status_code=400,
        )


def test_facebook_api_error_string_omits_raw_message() -> None:
    error = FacebookApiError(
        message="Sensitive diagnostic detail",
        status_code=401,
        code=190,
    )

    result = str(error)

    assert "HTTP 401" in result
    assert "code 190" in result
    assert "Sensitive diagnostic detail" not in result


def test_facebook_api_error_supports_transient_flag() -> None:
    error = FacebookApiError(
        message="Temporary failure",
        status_code=503,
        is_transient=True,
    )

    assert error.is_transient is True


@pytest.mark.parametrize("invalid_message", [
    "", "   ", None, 123,
])
def test_facebook_api_error_rejects_invalid_message(
    invalid_message,
) -> None:
    with pytest.raises(ValueError, match="message"):
        FacebookApiError(message=invalid_message)


@pytest.mark.parametrize("field_name", [
    "status_code", "code", "subcode",
])
def test_facebook_api_error_rejects_invalid_codes(
    field_name,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        FacebookApiError(
            message="Failure",
            **{field_name: True},
        )


def test_facebook_api_error_rejects_invalid_transient() -> None:
    with pytest.raises(ValueError, match="is_transient"):
        FacebookApiError(
            message="Failure",
            is_transient=cast(Any, "yes"),
        )


def test_facebook_api_error_rejects_invalid_type() -> None:
    with pytest.raises(ValueError, match="error type"):
        FacebookApiError(
            message="Failure",
            error_type=cast(Any, 123),
        )
