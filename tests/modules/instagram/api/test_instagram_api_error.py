import pytest

from socialflow.modules.instagram.api.instagram_api_error import (
    InstagramApiError,
)


def test_instagram_api_error_preserves_structured_fields() -> None:
    error = InstagramApiError(
        message="API request failed.",
        status_code=429,
        code=4,
        subcode=123,
        is_transient=True,
        error_type="OAuthException",
    )

    assert error.status_code == 429
    assert error.code == 4
    assert error.subcode == 123
    assert error.is_transient is True
    assert error.error_type == "OAuthException"


def test_instagram_api_error_has_safe_string_representation() -> None:
    error = InstagramApiError(
        message="Sensitive token: secret-value",
        status_code=400,
        code=190,
        subcode=463,
        error_type="SensitiveErrorType",
    )

    result = str(error)

    assert "Instagram API request failed" in result
    assert "HTTP 400" in result
    assert "code 190" in result
    assert "subcode 463" in result

    assert "secret-value" not in result
    assert "SensitiveErrorType" not in result


def test_instagram_api_error_trims_message() -> None:
    error = InstagramApiError(
        message="  Request failed.  ",
    )

    assert error.message == "Request failed."


@pytest.mark.parametrize(
    "message",
    ["", "   ", None, 123],
)
def test_instagram_api_error_rejects_invalid_message(
    message: object,
) -> None:
    with pytest.raises(ValueError):
        InstagramApiError(message=message)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ["status_code", "code", "subcode"],
)
def test_instagram_api_error_rejects_invalid_integer_fields(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        InstagramApiError(
            message="Request failed.",
            **{field_name: True},
        )


def test_instagram_api_error_rejects_invalid_transient_flag() -> None:
    with pytest.raises(ValueError):
        InstagramApiError(
            message="Request failed.",
            is_transient="yes",  # type: ignore[arg-type]
        )


def test_instagram_api_error_rejects_invalid_error_type() -> None:
    with pytest.raises(ValueError):
        InstagramApiError(
            message="Request failed.",
            error_type=123,  # type: ignore[arg-type]
        )


def test_instagram_api_error_is_an_exception() -> None:
    error = InstagramApiError(
        message="Request failed.",
    )

    assert isinstance(error, Exception)


def test_instagram_api_error_does_not_expose_message_in_repr() -> None:
    error = InstagramApiError(
        message="secret-value",
    )

    assert "secret-value" not in repr(error)