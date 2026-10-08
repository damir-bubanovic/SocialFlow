from PySide6.QtWidgets import QPlainTextEdit, QWidget
from pathlib import Path

from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.destination_selector import DestinationSelector
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_button import PublishButton
from socialflow.domain.post.tag import Tag


def create_facebook_account() -> Account:
    return Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )


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


def test_publish_button_is_disabled_without_account(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText("Hello from SocialFlow")

    assert not editor.publish_button.isEnabled()


def test_publish_button_is_enabled_with_content_and_account(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.set_accounts((create_facebook_account(),))
    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector._checkboxes[0].setChecked(True)

    assert editor.publish_button.isEnabled()


def test_publish_button_is_disabled_when_post_has_no_content(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.set_accounts((create_facebook_account(),))
    editor.destination_selector._checkboxes[0].setChecked(True)

    editor.text_editor.setPlainText("Hello")
    editor.text_editor.setPlainText("   ")

    assert not editor.publish_button.isEnabled()


def test_post_editor_emits_publish_request(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    account = create_facebook_account()
    editor.set_accounts((account,))
    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector._checkboxes[0].setChecked(True)

    with qtbot.waitSignal(editor.publish_requested) as blocker:
        editor.publish_button.click()

    request = blocker.args[0]

    assert isinstance(request, PublishRequest)
    assert request.post.text == "Hello from SocialFlow"
    assert request.post.language == Language.ENGLISH
    assert request.accounts == (account,)


def test_post_editor_contains_destination_selector(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert isinstance(editor.destination_selector, DestinationSelector)


def test_post_editor_returns_selected_accounts(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    facebook = create_facebook_account()
    instagram = Account(
        name="Main Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    editor.set_accounts((facebook, instagram))

    editor.destination_selector._checkboxes[0].setChecked(True)
    editor.destination_selector._checkboxes[1].setChecked(True)

    assert editor.selected_accounts() == (
        facebook,
        instagram,
    )


def test_publish_button_is_disabled_when_account_is_removed(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.set_accounts((create_facebook_account(),))
    editor.text_editor.setPlainText("Hello from SocialFlow")

    checkbox = editor.destination_selector._checkboxes[0]

    checkbox.setChecked(True)
    checkbox.setChecked(False)

    assert not editor.publish_button.isEnabled()


def test_post_editor_returns_publish_request(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    editor.set_accounts((account,))
    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector._checkboxes[0].setChecked(True)

    request = editor.publish_request()

    assert request.post.text == "Hello from SocialFlow"
    assert request.accounts == (account,)

def test_post_contains_selected_images(
    qtbot,
    tmp_path: Path,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    image_path = tmp_path / "socialflow-image.jpg"
    image_path.touch()

    image = ImageAttachment(path=image_path)

    editor.image_selector._images = (image,)

    post = editor.post()

    assert post.images == (image,)

def test_post_editor_includes_selected_tags_in_publish_request(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    account = create_facebook_account()

    editor.set_accounts((account,))
    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.destination_selector._checkboxes[0].setChecked(True)

    editor.tag_selector.tag_input.setText("SocialFlow")
    editor.tag_selector.add_button.click()

    requests = []
    editor.publish_requested.connect(requests.append)

    editor.publish_button.click()

    assert len(requests) == 1
    assert requests[0].post.tags == (
        Tag(name="SocialFlow"),
    )
    assert requests[0].accounts == (account,)

def test_tag_creation_is_disabled_without_selected_account(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    assert not editor.tag_selector.tag_input.isEnabled()
    assert not editor.tag_selector.add_button.isEnabled()

def test_tag_creation_is_enabled_when_account_is_selected(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.set_accounts((create_facebook_account(),))
    editor.destination_selector._checkboxes[0].setChecked(True)

    assert editor.tag_selector.tag_input.isEnabled()
    assert editor.tag_selector.add_button.isEnabled()

def test_tag_creation_is_disabled_when_account_is_deselected(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.set_accounts((create_facebook_account(),))

    checkbox = editor.destination_selector._checkboxes[0]

    checkbox.setChecked(True)

    assert editor.tag_selector.tag_input.isEnabled()
    assert editor.tag_selector.add_button.isEnabled()

    checkbox.setChecked(False)

    assert not editor.tag_selector.tag_input.isEnabled()
    assert not editor.tag_selector.add_button.isEnabled()

def test_post_editor_loads_post_text(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    post = Post(
        text="Historical publication",
        language=Language.ENGLISH,
    )

    editor.load_post(post)

    assert editor.post_text() == "Historical publication"


def test_post_editor_loads_post_language(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    post = Post(
        text="Historical publication",
        language=Language.ENGLISH,
    )

    editor.load_post(post)

    assert editor.selected_language() == Language.ENGLISH

def test_post_editor_loads_post_tags(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    post = Post(
        text="Historical publication",
        language=Language.ENGLISH,
        tags=(
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        ),
    )

    editor.load_post(post)

    assert editor.tag_selector.selected_tags() == (
        Tag(name="SocialFlow"),
        Tag(name="Python"),
    )

def test_post_editor_loads_post_images(
    qtbot,
    tmp_path,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    image_path = tmp_path / "historical.jpg"
    image_path.touch()

    image = ImageAttachment(path=image_path)

    post = Post(
        text="Historical publication",
        language=Language.ENGLISH,
        images=(image,),
    )

    editor.load_post(post)

    assert editor.image_selector.selected_images() == (
        image,
    )

def test_post_editor_automatically_detects_croatian(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert editor.selected_language() is Language.ENGLISH

    editor.text_editor.setPlainText(
        "Danas ćemo objaviti važnu obavijest."
    )

    assert editor.selected_language() is Language.CROATIAN
    assert editor.language_controls.indicator.text() == "HR"

def test_manual_language_selection_is_preserved_when_text_changes(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.language_controls.set_language(Language.CROATIAN)

    editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert editor.selected_language() is Language.CROATIAN

def test_dropdown_language_selection_prevents_automatic_detection(
    qtbot,
) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.language_controls.selector.activated.emit(
        editor.language_controls.selector.currentIndex()
    )

    editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert editor.selected_language() is Language.CROATIAN

def test_new_post_resets_manual_language_override(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    editor.language_controls.set_language(Language.CROATIAN)

    editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert editor.selected_language() is Language.CROATIAN

    editor.new_post()

    assert editor.post_text() == ""

    editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert editor.selected_language() is Language.ENGLISH

def test_new_post_clears_content_but_preserves_accounts(qtbot) -> None:
    editor = PostEditor()
    qtbot.addWidget(editor)

    account = create_facebook_account()
    editor.set_accounts((account,))
    editor.destination_selector._checkboxes[0].setChecked(True)

    editor.text_editor.setPlainText("Hello from SocialFlow")
    editor.new_post()

    assert editor.post_text() == ""
    assert editor.image_selector.selected_images() == ()
    assert editor.tag_selector.selected_tags() == ()
    assert editor.selected_accounts() == (account,)
    assert not editor.publish_button.isEnabled()