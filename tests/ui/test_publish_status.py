from socialflow.ui.posts.publish_status import PublishStatus


def test_publish_status_is_empty_by_default(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    assert status.text() == ""
    assert status.property("status") == ""


def test_publish_status_can_show_success(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_success()

    assert status.text() == "Publish request completed."
    assert status.property("status") == "success"


def test_publish_status_can_be_cleared(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_success()
    status.clear_status()

    assert status.text() == ""
    assert status.property("status") == ""

def test_publish_status_can_show_error(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_error()

    assert status.text() == "Publish request failed."
    assert status.property("status") == "error"