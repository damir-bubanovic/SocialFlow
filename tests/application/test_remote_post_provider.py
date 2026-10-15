import pytest

from socialflow.application.publishing.remote_post_provider import (
    RemotePostProvider,
)


def test_remote_post_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        RemotePostProvider()