from PySide6.QtWidgets import QPlainTextEdit, QWidget

from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.destination_selector import DestinationSelector
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_button import PublishButton


def test_post_editor_is_widget(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor, QWidget)


def test_post_editor_contains_text_editor(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor.text_editor, QPlainTextEdit)


def test_post_editor_has_placeholder(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert editor.text_editor.placeholderText() == "Write your post..."


def test_post_editor_contains_language_controls(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor.language_controls, LanguageControls)


def test_post_editor_language_can_be_changed(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.language_controls.selector.setCurrentIndex(1)

    assert editor.selected_language() == Language.ENGLISH
    assert editor.language_controls.indicator.text() == "EN"


def test_post_editor_returns_post_text(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")

    assert editor.post_text() == "Hello from SocialFlow"


def test_post_editor_returns_post(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.language_controls.selector.setCurrentIndex(1)

    post = editor.post()

    assert isinstance(post, Post)
    assert post.text == "Hello from SocialFlow"
    assert post.language == Language.ENGLISH


def test_post_editor_contains_publish_button(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor.publish_button, PublishButton)


def test_publish_button_is_disabled_without_destination(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")

    assert not editor.publish_button.isEnabled()


def test_publish_button_is_enabled_with_content_and_destination(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector.facebook.setChecked(True)

    assert editor.publish_button.isEnabled()


def test_publish_button_is_disabled_when_post_has_no_content(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.destination_selector.facebook.setChecked(True)
    editor.text_editor.setPlainText("Hello")
    editor.text_editor.setPlainText("   ")

    assert not editor.publish_button.isEnabled()


def test_post_editor_emits_publish_request(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector.facebook.setChecked(True)

    with qtbot.waitSignal(editor.publish_requested) as blocker:
        editor.publish_button.click()

    request = blocker.args[0]

    assert isinstance(request, PublishRequest)
    assert request.post.text == "Hello from SocialFlow"
    assert request.post.language == Language.CROATIAN
    assert request.destinations == (
        PublishingDestination.FACEBOOK,
    )


def test_post_editor_contains_destination_selector(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor.destination_selector, DestinationSelector)


def test_post_editor_returns_selected_destinations(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.destination_selector.facebook.setChecked(True)
    editor.destination_selector.instagram.setChecked(True)

    assert editor.selected_destinations() == (
        PublishingDestination.FACEBOOK,
        PublishingDestination.INSTAGRAM,
    )


def test_publish_button_is_disabled_when_destination_is_removed(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector.facebook.setChecked(True)
    editor.destination_selector.facebook.setChecked(False)

    assert not editor.publish_button.isEnabled()


def test_post_editor_returns_publish_request(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector.wordpress.setChecked(True)

    request = editor.publish_request()

    assert request.post.text == "Hello from SocialFlow"
    assert request.destinations == (
        PublishingDestination.WORDPRESS,
    )
