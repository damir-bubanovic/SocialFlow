import pytest

from socialflow.application.publishing.error_classifier import (
    ErrorCategory,
    ErrorClassifier,
)
from socialflow.application.publishing.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
    PublisherNotConfiguredError,
    PublishingError,
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