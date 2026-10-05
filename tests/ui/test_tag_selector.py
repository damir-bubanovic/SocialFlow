from PySide6.QtWidgets import QCheckBox, QWidget

from socialflow.domain.post.tag import Tag
from socialflow.ui.posts.tag_selector import TagSelector


def test_tag_selector_is_widget(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    assert isinstance(selector, QWidget)


def test_tag_selector_starts_without_tags(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    assert selector.available_tags() == ()
    assert selector.selected_tags() == ()
    assert selector.status_label.text() == "No tags selected."
    assert selector.selected_tags_label.text() == ""


def test_tag_selector_stores_available_tags(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    tags = (
        Tag(name="SocialFlow"),
        Tag(name="Python"),
    )

    selector.set_available_tags(tags)

    assert selector.available_tags() == tags


def test_tag_selector_adds_entered_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector.status_label.text() == "1 tag(s) selected."
    assert selector.selected_tags_label.text() == "SocialFlow"
    assert selector.tag_input.text() == ""


def test_tag_selector_does_not_add_empty_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.tag_input.setText("   ")
    selector.add_button.click()

    assert selector.selected_tags() == ()
    assert selector.status_label.text() == "No tags selected."


def test_tag_selector_does_not_add_duplicate_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector.status_label.text() == "1 tag(s) selected."

def test_tag_selector_displays_available_tags(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
    )

    assert len(selector._tag_checkboxes) == 2
    assert all(
        isinstance(checkbox, QCheckBox)
        for checkbox in selector._tag_checkboxes
    )
    assert [
        checkbox.text()
        for checkbox in selector._tag_checkboxes
    ] == [
        "SocialFlow",
        "Python",
    ]

def test_tag_selector_selects_available_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
    )

    selector._tag_checkboxes[0].setChecked(True)

    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector.status_label.text() == "1 tag(s) selected."
    assert selector.selected_tags_label.text() == "SocialFlow"

def test_tag_selector_deselects_available_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
        )
    )

    checkbox = selector._tag_checkboxes[0]

    checkbox.setChecked(True)
    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )

    checkbox.setChecked(False)

    assert selector.selected_tags() == ()
    assert selector.status_label.text() == "No tags selected."
    assert selector.selected_tags_label.text() == ""

def test_entering_available_tag_selects_its_checkbox(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
    )

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector._tag_checkboxes[0].isChecked()
    assert not selector._tag_checkboxes[1].isChecked()

def test_entering_new_tag_does_not_change_available_checkboxes(
    qtbot,
) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
    )

    selector.tag_input.setText("Qt")
    selector.add_button.click()

    assert selector.selected_tags() == (
        Tag(name="Qt"),
    )
    assert not selector._tag_checkboxes[0].isChecked()
    assert not selector._tag_checkboxes[1].isChecked()

def test_entering_already_selected_available_tag_does_not_duplicate_it(
    qtbot,
) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
        )
    )

    selector._tag_checkboxes[0].setChecked(True)

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector._tag_checkboxes[0].isChecked()
    assert selector.status_label.text() == "1 tag(s) selected."

def test_tag_selector_can_remove_manually_entered_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    tag = selector.selected_tags()[0]
    selector.remove_tag(tag)

    assert selector.selected_tags() == ()
    assert selector.status_label.text() == "No tags selected."
    assert selector.selected_tags_label.text() == ""


def test_tag_selector_remove_tag_unchecks_available_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    tag = Tag(name="SocialFlow")

    selector.set_available_tags((tag,))
    selector._tag_checkboxes[0].setChecked(True)

    selector.remove_tag(tag)

    assert selector.selected_tags() == ()
    assert not selector._tag_checkboxes[0].isChecked()
    assert selector.status_label.text() == "No tags selected."


def test_tag_selector_can_clear_selected_tags(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
    )

    selector._tag_checkboxes[0].setChecked(True)
    selector._tag_checkboxes[1].setChecked(True)

    selector.tag_input.setText("Qt")
    selector.add_button.click()

    assert len(selector.selected_tags()) == 3

    selector.clear_button.click()

    assert selector.selected_tags() == ()
    assert selector.status_label.text() == "No tags selected."
    assert selector.selected_tags_label.text() == ""
    assert all(
        not checkbox.isChecked()
        for checkbox in selector._tag_checkboxes
    )

def test_tag_selector_emits_tag_created_for_new_tag(qtbot) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    with qtbot.waitSignal(selector.tag_created) as blocker:
        selector.tag_input.setText("SocialFlow")
        selector.add_button.click()

    assert blocker.args == [
        Tag(name="SocialFlow"),
    ]


def test_tag_selector_does_not_emit_tag_created_for_available_tag(
    qtbot,
) -> None:
    selector = TagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags(
        (
            Tag(name="SocialFlow"),
        )
    )

    emitted_tags = []
    selector.tag_created.connect(emitted_tags.append)

    selector.tag_input.setText("SocialFlow")
    selector.add_button.click()

    assert emitted_tags == []
    assert selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert selector._tag_checkboxes[0].isChecked()