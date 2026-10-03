from socialflow.ui.posts.publish_button import PublishButton


def test_publish_button_is_disabled_by_default(qtbot) -> None:
    button = PublishButton()
    qtbot.addWidget(button)

    assert not button.isEnabled()


def test_publish_button_can_be_enabled(qtbot) -> None:
    button = PublishButton()
    qtbot.addWidget(button)

    button.set_post_available(True)

    assert button.isEnabled()


def test_publish_button_can_be_disabled(qtbot) -> None:
    button = PublishButton()
    qtbot.addWidget(button)

    button.set_post_available(True)
    button.set_post_available(False)

    assert not button.isEnabled()