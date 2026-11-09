import pytest

from socialflow.modules.posts.services.error_classifier import (
    ErrorCategory,
    ErrorClassifier,
)
from socialflow.modules.posts.services.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
    PublisherNotConfiguredError,
    PublishingError,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)


@pytest.mark.parametrize(
    "error",
    [
        ConnectionError("Connection lost."),
        TimeoutError("Request timed out."),
    ],
)
def test_classifies_transient_errors(error: Exception) -> None:
    assert ErrorClassifier.classify(error) is ErrorCategory.TRANSIENT


@pytest.mark.parametrize(
    "error",
    [
        EmptyPostError("Post is empty."),
        PublisherNotConfiguredError("Publisher missing."),
        ImagePreparationNotConfiguredError("Image preparation missing."),
    ],
)
def test_classifies_permanent_errors(error: Exception) -> None:
    assert ErrorClassifier.classify(error) is ErrorCategory.PERMANENT


@pytest.mark.parametrize(
    "error",
    [
        PublishingError("Unexpected platform error."),
        ValueError("Unexpected value."),
        RuntimeError("Unexpected runtime failure."),
    ],
)
def test_classifies_unknown_errors(error: Exception) -> None:
    assert ErrorClassifier.classify(error) is ErrorCategory.UNKNOWN


def test_classifies_transient_facebook_api_error() -> None:
    error = FacebookApiError(
        message="Facebook service temporarily unavailable.",
        status_code=503,
        is_transient=True,
    )

    assert ErrorClassifier.classify(error) is ErrorCategory.TRANSIENT


def test_classifies_permanent_facebook_api_error() -> None:
    error = FacebookApiError(
        message="Facebook access token rejected.",
        status_code=400,
        code=190,
        is_transient=False,
    )

    assert ErrorClassifier.classify(error) is ErrorCategory.PERMANENT
