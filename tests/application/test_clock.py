import pytest

from socialflow.application.time.clock import Clock


def test_clock_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        Clock()