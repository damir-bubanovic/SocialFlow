from PySide6.QtWidgets import QPlainTextEdit, QWidget

from socialflow.domain.language.language import Language
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.domain.post.post import Post
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


def test_publish_button_is_enabled_when_post_has_content(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")

    assert editor.publish_button.isEnabled()


def test_publish_button_is_disabled_when_post_has_no_content(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello")
    editor.text_editor.setPlainText("   ")

    assert not editor.publish_button.isEnabled()

def test_post_editor_emits_post_when_publish_is_requested(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")

    with qtbot.waitSignal(editor.publish_requested) as blocker:
        editor.publish_button.click()

    emitted_post = blocker.args[0]

    assert isinstance(emitted_post, Post)
    assert emitted_post.text == "Hello from SocialFlow"
    assert emitted_post.language == Language.CROATIAN