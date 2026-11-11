from collections.abc import Callable
from typing import cast
from unittest.mock import Mock, call

import pytest

from socialflow.modules.instagram.api.instagram_graph_client import (
    InstagramGraphClient,
)
from socialflow.modules.instagram.services.instagram_publishing_service import (
    InstagramPublishingService,
)


def test_create_image_container_uses_instagram_graph_api() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}

    service = InstagramPublishingService(client)

    container_id = service.create_image_container(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        caption="Test Instagram caption",
    )

    assert container_id == "17890000000000001"

    client.post.assert_called_once_with(
        path="123456789/media",
        access_token="test-access-token",
        params={
            "image_url": "https://example.com/photo.jpg",
            "caption": "Test Instagram caption",
        },
    )


@pytest.mark.parametrize(
    "instagram_user_id,access_token,image_url",
    [
        ("", "token", "https://example.com/photo.jpg"),
        ("123456789", "", "https://example.com/photo.jpg"),
        ("123456789", "token", ""),
        ("123456789", "token", "file:///tmp/photo.jpg"),
        ("123456789", "token", "http://example.com/photo.jpg"),
    ],
)
def test_create_image_container_rejects_invalid_inputs(
    instagram_user_id: str,
    access_token: str,
    image_url: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.create_image_container(
            instagram_user_id=instagram_user_id,
            access_token=access_token,
            image_url=image_url,
            caption="Test caption",
        )

    client.post.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"id": ""},
        {"id": None},
        {"id": 12345},
    ],
)
def test_create_image_container_rejects_invalid_response(
    response: dict,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = response

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="container ID"):
        service.create_image_container(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )


@pytest.mark.parametrize(
    "instagram_user_id",
    [
        "123/456",
        "../123",
        "123?fields=id",
        "123#fragment",
        "123 456",
        "123\\456",
        "https://example.com",
        "１２３",
    ],
)
def test_create_image_container_rejects_unsafe_user_ids(
    instagram_user_id: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.create_image_container(
            instagram_user_id=instagram_user_id,
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    client.post.assert_not_called()


@pytest.mark.parametrize(
    "image_url",
    [
        "https://example.com:invalid/photo.jpg",
        "https://example.com:99999/photo.jpg",
        "https://example.com/photo.jpg#fragment",
        "https://example.com/photo.jpg?token=secret",
        "https://localhost/photo.jpg",
        "https://127.0.0.1/photo.jpg",
        "https://192.168.1.10/photo.jpg",
        "https://10.0.0.1/photo.jpg",
        "https://172.16.0.1/photo.jpg",
        "https://[::1]/photo.jpg",
        "https://169.254.169.254/photo.jpg",
        "https://user:password@example.com/photo.jpg",
        "https://example.com\\@localhost/photo.jpg",
        "https://[invalid/photo.jpg",
    ],
)
def test_create_image_container_rejects_unsafe_image_urls(
    image_url: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.create_image_container(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url=image_url,
        )

    client.post.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        "IN_PROGRESS",
        "FINISHED",
        "ERROR",
        "EXPIRED",
    ],
)
def test_get_container_status_returns_valid_status(
    status: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    result = service.get_container_status(
        container_id="17890000000000001",
        access_token="test-access-token",
    )

    assert result == status

    client.get.assert_called_once_with(
        path="17890000000000001",
        access_token="test-access-token",
        params={"fields": "status_code"},
    )


@pytest.mark.parametrize(
    "container_id,access_token",
    [
        ("", "token"),
        ("123/456", "token"),
        ("../123", "token"),
        ("123?fields=id", "token"),
        ("123#fragment", "token"),
        ("123 456", "token"),
        ("１２３", "token"),
        ("123456789", ""),
        ("123456789", "   "),
    ],
)
def test_get_container_status_rejects_invalid_inputs(
    container_id: str,
    access_token: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.get_container_status(
            container_id=container_id,
            access_token=access_token,
        )

    client.get.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"status_code": None},
        {"status_code": ""},
        {"status_code": 123},
        {"status_code": "UNKNOWN"},
        {"status_code": "finished"},
    ],
)
def test_get_container_status_rejects_invalid_response(
    response: dict,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = response

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="status"):
        service.get_container_status(
            container_id="17890000000000001",
            access_token="test-access-token",
        )


def test_get_container_status_propagates_api_errors() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    error = InstagramApiError(
        message="Instagram request failed.",
        status_code=503,
        is_transient=True,
    )
    client.get.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.get_container_status(
            container_id="17890000000000001",
            access_token="test-access-token",
        )

    assert caught.value is error
    client.get.assert_called_once()


def test_publish_media_container_success() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "FINISHED"}
    client.post.return_value = {"id": "17900000000000001"}

    service = InstagramPublishingService(client)

    result = service.publish_media_container(
        instagram_user_id="123456789",
        container_id="17890000000000001",
        access_token="test-access-token",
    )

    assert result == "17900000000000001"

    client.get.assert_called_once_with(
        path="17890000000000001",
        access_token="test-access-token",
        params={"fields": "status_code"},
    )

    client.post.assert_called_once_with(
        path="123456789/media_publish",
        access_token="test-access-token",
        params={"creation_id": "17890000000000001"},
    )


@pytest.mark.parametrize(
    "status",
    [
        "IN_PROGRESS",
        "ERROR",
        "EXPIRED",
    ],
)
def test_publish_media_container_rejects_unfinished_container(
    status: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="FINISHED"):
        service.publish_media_container(
            instagram_user_id="123456789",
            container_id="17890000000000001",
            access_token="test-access-token",
        )

    client.get.assert_called_once()
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "instagram_user_id,container_id,access_token",
    [
        ("", "17890000000000001", "token"),
        ("123/456", "17890000000000001", "token"),
        ("１２３", "17890000000000001", "token"),
        ("123456789", "", "token"),
        ("123456789", "../123", "token"),
        ("123456789", "123?fields=id", "token"),
        ("123456789", "１２３", "token"),
        ("123456789", "17890000000000001", ""),
        ("123456789", "17890000000000001", "   "),
    ],
)
def test_publish_media_container_rejects_invalid_inputs(
    instagram_user_id: str,
    container_id: str,
    access_token: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.publish_media_container(
            instagram_user_id=instagram_user_id,
            container_id=container_id,
            access_token=access_token,
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"id": None},
        {"id": ""},
        {"id": "   "},
        {"id": 123},
        {"id": "123/456"},
        {"id": "１２３"},
    ],
)
def test_publish_media_container_rejects_invalid_response(
    response: dict,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "FINISHED"}
    client.post.return_value = response

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="media ID"):
        service.publish_media_container(
            instagram_user_id="123456789",
            container_id="17890000000000001",
            access_token="test-access-token",
        )

    client.get.assert_called_once()
    client.post.assert_called_once()


def test_publish_media_container_propagates_status_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    error = InstagramApiError(
        message="Status request failed.",
        status_code=503,
        is_transient=True,
    )
    client.get.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.publish_media_container(
            instagram_user_id="123456789",
            container_id="17890000000000001",
            access_token="test-access-token",
        )

    assert caught.value is error
    client.post.assert_not_called()


def test_publish_media_container_propagates_publish_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "FINISHED"}

    error = InstagramApiError(
        message="Publishing failed.",
        status_code=500,
        is_transient=True,
    )
    client.post.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.publish_media_container(
            instagram_user_id="123456789",
            container_id="17890000000000001",
            access_token="test-access-token",
        )

    assert caught.value is error
    client.get.assert_called_once()
    client.post.assert_called_once()


def test_publish_image_success() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        caption="Test caption",
    )

    assert result == "17900000000000001"

    assert client.post.call_args_list == [
        call(
            path="123456789/media",
            access_token="test-access-token",
            params={
                "image_url": "https://example.com/photo.jpg",
                "caption": "Test caption",
            },
        ),
        call(
            path="123456789/media_publish",
            access_token="test-access-token",
            params={
                "creation_id": "17890000000000001",
            },
        ),
    ]

    assert client.get.call_count == 2


@pytest.mark.parametrize(
    "status",
    [
        "ERROR",
        "EXPIRED",
    ],
)
def test_publish_image_rejects_unfinished_container(
    status: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="FINISHED"):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    client.get.assert_called_once()
    client.post.assert_called_once_with(
        path="123456789/media",
        access_token="test-access-token",
        params={
            "image_url": "https://example.com/photo.jpg",
            "caption": "",
        },
    )


def test_publish_image_rejects_invalid_input_before_api_calls() -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.publish_image(
            instagram_user_id="123/456",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


def test_publish_image_propagates_creation_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    error = InstagramApiError(
        message="Container creation failed.",
        status_code=503,
        is_transient=True,
    )
    client.post.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    assert caught.value is error
    client.get.assert_not_called()
    client.post.assert_called_once()


def test_publish_image_propagates_status_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}

    error = InstagramApiError(
        message="Status request failed.",
        status_code=503,
        is_transient=True,
    )
    client.get.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    assert caught.value is error
    client.get.assert_called_once()
    client.post.assert_called_once()


def test_publish_image_propagates_publish_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)
    error = InstagramApiError(
        message="Publishing failed.",
        status_code=500,
        is_transient=True,
    )

    client.post.side_effect = [
        {"id": "17890000000000001"},
        error,
    ]
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)


    with pytest.raises(InstagramApiError) as caught:
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    assert caught.value is error
    assert client.get.call_count == 2
    assert client.post.call_count == 2


def test_wait_for_container_ready_finishes_immediately() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)

    result = service.wait_for_container_ready(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=3,
    )

    assert result == "FINISHED"
    client.get.assert_called_once_with(
        path="17890000000000001",
        access_token="test-access-token",
        params={"fields": "status_code"},
    )
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "statuses",
    [
        ["IN_PROGRESS", "FINISHED"],
        ["IN_PROGRESS", "IN_PROGRESS", "FINISHED"],
    ],
)
def test_wait_for_container_ready_retries_until_finished(
    statuses: list[str],
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.side_effect = [
        {"status_code": status}
        for status in statuses
    ]

    service = InstagramPublishingService(client)

    result = service.wait_for_container_ready(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=3,
    )

    assert result == "FINISHED"
    assert client.get.call_count == len(statuses)
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "status",
    ["ERROR", "EXPIRED"],
)
def test_wait_for_container_ready_stops_on_terminal_failure(
    status: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match=status):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
        )

    client.get.assert_called_once()
    client.post.assert_not_called()


def test_wait_for_container_ready_exhausts_attempts() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "IN_PROGRESS"}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="IN_PROGRESS"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
        )

    assert client.get.call_count == 3
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "max_attempts",
    [
        0,
        -1,
        True,
        False,
        1.5,
        "3",
        None,
    ],
)
def test_wait_for_container_ready_rejects_invalid_attempt_count(
    max_attempts: object,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="max_attempts"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=cast(int, max_attempts),
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


def test_wait_for_container_ready_rejects_invalid_credentials() -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.wait_for_container_ready(
            container_id="../123",
            access_token="test-access-token",
            max_attempts=3,
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


def test_wait_for_container_ready_propagates_api_error() -> None:
    from socialflow.modules.instagram.api.instagram_api_error import (
        InstagramApiError,
    )

    client = Mock(spec=InstagramGraphClient)

    error = InstagramApiError(
        message="Status request failed.",
        status_code=503,
        is_transient=True,
    )
    client.get.side_effect = error

    service = InstagramPublishingService(client)

    with pytest.raises(InstagramApiError) as caught:
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
        )

    assert caught.value is error
    client.get.assert_called_once()
    client.post.assert_not_called()


def test_wait_for_container_ready_sleeps_between_checks() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.get.side_effect = [
        {"status_code": "IN_PROGRESS"},
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
    ]

    service = InstagramPublishingService(client)

    result = service.wait_for_container_ready(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=3,
        poll_interval_seconds=2.0,
        sleep=sleep,
    )

    assert result == "FINISHED"
    assert client.get.call_count == 3
    assert sleep.call_args_list == [
        call(2.0),
        call(2.0),
    ]


def test_wait_for_container_ready_does_not_sleep_on_immediate_success() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)

    result = service.wait_for_container_ready(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=3,
        poll_interval_seconds=2.0,
        sleep=sleep,
    )

    assert result == "FINISHED"
    client.get.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "status",
    ["ERROR", "EXPIRED"],
)
def test_wait_for_container_ready_does_not_sleep_on_terminal_failure(
    status: str,
) -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match=status):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
            poll_interval_seconds=2.0,
            sleep=sleep,
        )

    client.get.assert_called_once()
    sleep.assert_not_called()


def test_wait_for_container_ready_does_not_sleep_after_final_attempt() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "IN_PROGRESS"}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="IN_PROGRESS"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
            poll_interval_seconds=2.0,
            sleep=sleep,
        )

    assert client.get.call_count == 3
    assert sleep.call_args_list == [
        call(2.0),
        call(2.0),
    ]


def test_wait_for_container_ready_allows_zero_interval() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.get.side_effect = [
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
    ]

    service = InstagramPublishingService(client)

    result = service.wait_for_container_ready(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=2,
        poll_interval_seconds=0.0,
        sleep=sleep,
    )

    assert result == "FINISHED"
    assert client.get.call_count == 2
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "poll_interval_seconds",
    [
        -1,
        True,
        False,
        "2",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_wait_for_container_ready_rejects_invalid_poll_interval(
    poll_interval_seconds: object,
) -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="poll_interval_seconds"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
            poll_interval_seconds=cast(float, poll_interval_seconds),
            sleep=sleep,
        )

    client.get.assert_not_called()
    client.post.assert_not_called()
    sleep.assert_not_called()


def test_wait_for_container_ready_rejects_non_callable_sleep() -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="sleep"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
            poll_interval_seconds=2.0,
            sleep=cast("Callable[[float], None]", "not-callable"),
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


def test_wait_for_container_ready_propagates_sleep_error() -> None:
    sleep = Mock(side_effect=RuntimeError("Interrupted"))
    client = Mock(spec=InstagramGraphClient)
    client.get.return_value = {"status_code": "IN_PROGRESS"}

    service = InstagramPublishingService(client)

    with pytest.raises(RuntimeError, match="Interrupted"):
        service.wait_for_container_ready(
            container_id="17890000000000001",
            access_token="test-access-token",
            max_attempts=3,
            poll_interval_seconds=2.0,
            sleep=sleep,
        )

    client.get.assert_called_once()
    sleep.assert_called_once_with(2.0)
    client.post.assert_not_called()


def test_publish_image_uses_container_ready_waiter() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)
    service.wait_for_container_ready = Mock(return_value="FINISHED")

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        caption="Test caption",
    )

    assert result == "17900000000000001"
    kwargs = service.wait_for_container_ready.call_args.kwargs

    assert kwargs["container_id"] == "17890000000000001"
    assert kwargs["access_token"] == "test-access-token"
    assert kwargs["max_attempts"] == 3
    assert kwargs["poll_interval_seconds"] == 2.0
    assert callable(kwargs["sleep"])
    client.post.assert_called_with(
        path="123456789/media_publish",
        access_token="test-access-token",
        params={"creation_id": "17890000000000001"},
    )


def test_publish_image_polls_until_container_finished() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.side_effect = [
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
        {"status_code": "FINISHED"},
    ]

    service = InstagramPublishingService(client)

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        caption="Test caption",
        sleep=sleep,
    )

    assert result == "17900000000000001"
    assert client.get.call_count == 3
    assert client.post.call_count == 2
    sleep.assert_called_once_with(2.0)


def test_publish_image_stops_after_polling_exhausted() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}
    client.get.return_value = {"status_code": "IN_PROGRESS"}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="IN_PROGRESS"):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    assert client.get.call_count == 3
    client.post.assert_called_once()


@pytest.mark.parametrize(
    "status",
    ["ERROR", "EXPIRED"],
)
def test_publish_image_stops_on_terminal_container_status(
    status: str,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}
    client.get.return_value = {"status_code": status}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match=status):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
        )

    client.get.assert_called_once()
    client.post.assert_called_once()


def test_publish_image_passes_polling_configuration_to_waiter() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)
    service.wait_for_container_ready = Mock(return_value="FINISHED")

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        caption="Test caption",
        max_attempts=5,
        poll_interval_seconds=2.0,
        sleep=sleep,
    )

    assert result == "17900000000000001"
    service.wait_for_container_ready.assert_called_once_with(
        container_id="17890000000000001",
        access_token="test-access-token",
        max_attempts=5,
        poll_interval_seconds=2.0,
        sleep=sleep,
    )


def test_publish_image_uses_production_polling_defaults() -> None:
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.return_value = {"status_code": "FINISHED"}

    service = InstagramPublishingService(client)
    service.wait_for_container_ready = Mock(return_value="FINISHED")

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
    )

    assert result == "17900000000000001"

    kwargs = service.wait_for_container_ready.call_args.kwargs

    assert kwargs["container_id"] == "17890000000000001"
    assert kwargs["access_token"] == "test-access-token"
    assert kwargs["max_attempts"] == 3
    assert kwargs["poll_interval_seconds"] == 2.0
    assert callable(kwargs["sleep"])


def test_publish_image_waits_between_processing_checks() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.post.side_effect = [
        {"id": "17890000000000001"},
        {"id": "17900000000000001"},
    ]
    client.get.side_effect = [
        {"status_code": "IN_PROGRESS"},
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
        {"status_code": "FINISHED"},
    ]

    service = InstagramPublishingService(client)

    result = service.publish_image(
        instagram_user_id="123456789",
        access_token="test-access-token",
        image_url="https://example.com/photo.jpg",
        max_attempts=4,
        poll_interval_seconds=2.0,
        sleep=sleep,
    )

    assert result == "17900000000000001"
    assert client.get.call_count == 4
    assert client.post.call_count == 2
    assert sleep.call_args_list == [
        call(2.0),
        call(2.0),
    ]


def test_publish_image_uses_custom_attempt_limit() -> None:
    sleep = Mock()
    client = Mock(spec=InstagramGraphClient)
    client.post.return_value = {"id": "17890000000000001"}
    client.get.return_value = {"status_code": "IN_PROGRESS"}

    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="IN_PROGRESS"):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
            max_attempts=2,
            poll_interval_seconds=1.5,
            sleep=sleep,
        )

    assert client.get.call_count == 2
    client.post.assert_called_once()
    sleep.assert_called_once_with(1.5)


@pytest.mark.parametrize(
    "max_attempts,poll_interval_seconds",
    [
        (0, 2.0),
        (-1, 2.0),
        (True, 2.0),
        (3, -1.0),
        (3, float("nan")),
        (3, float("inf")),
    ],
)
def test_publish_image_rejects_invalid_polling_configuration_before_api(
    max_attempts: object,
    poll_interval_seconds: object,
) -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
            max_attempts=cast(int, max_attempts),
            poll_interval_seconds=cast(float, poll_interval_seconds),
        )

    client.get.assert_not_called()
    client.post.assert_not_called()


def test_publish_image_rejects_invalid_sleep_before_api() -> None:
    client = Mock(spec=InstagramGraphClient)
    service = InstagramPublishingService(client)

    with pytest.raises(ValueError, match="sleep"):
        service.publish_image(
            instagram_user_id="123456789",
            access_token="test-access-token",
            image_url="https://example.com/photo.jpg",
            max_attempts=3,
            poll_interval_seconds=2.0,
            sleep=cast(Callable[[float], None], "not-callable"),
        )

    client.get.assert_not_called()
    client.post.assert_not_called()
