from socialflow.constants import (
    APP_NAME,
    APP_ORGANIZATION,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
)


def test_application_constants() -> None:
    assert APP_NAME == "SocialFlow"
    assert APP_ORGANIZATION == "SocialFlow"
    assert DEFAULT_WINDOW_WIDTH == 1200
    assert DEFAULT_WINDOW_HEIGHT == 800