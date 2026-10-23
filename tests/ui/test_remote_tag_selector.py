
from PySide6.QtCore import Qt
from unittest.mock import Mock

from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.ui.posts.remote_tag_selector import RemoteTagSelector


def test_remote_tag_selector_starts_empty(qtbot) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    assert selector.available_tags() == ()
    assert selector.selected_ids() == ()
    assert selector.tags_list.count() == 0


def test_remote_tag_selector_displays_names_and_ids(qtbot) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    tags = (
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    )

    selector.set_available_tags(tags)

    assert selector.available_tags() == tags
    assert selector.tags_list.count() == 2
    assert selector.tags_list.item(0).text() == "Python"
    assert selector.tags_list.item(1).text() == "SocialFlow"

    assert (
        selector.tags_list.item(0).data(Qt.ItemDataRole.UserRole)
        == 12
    )


def test_remote_tag_selector_preserves_existing_selection(qtbot) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    selector.set_selected_ids((34, 12))
    selector.set_available_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    ))

    assert selector.selected_ids() == (34, 12)
    assert (
        selector.tags_list.item(0).checkState()
        == Qt.CheckState.Checked
    )
    assert (
        selector.tags_list.item(1).checkState()
        == Qt.CheckState.Checked
    )


def test_remote_tag_selector_updates_ids_when_checked(qtbot) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    selector.set_available_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    ))

    changed = Mock()
    selector.selection_changed.connect(changed)

    selector.tags_list.item(1).setCheckState(
        Qt.CheckState.Checked
    )

    assert selector.selected_ids() == (34,)
    changed.assert_called_once_with()

    selector.tags_list.item(1).setCheckState(
        Qt.CheckState.Unchecked
    )

    assert selector.selected_ids() == ()
    assert changed.call_count == 2


def test_remote_tag_selector_preserves_unknown_ids(qtbot) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    selector.set_selected_ids((99,))
    selector.set_available_tags((
        RemoteTag(remote_id=12, name="Python"),
    ))

    assert selector.selected_ids() == (99,)
    assert selector.tags_list.count() == 2
    assert selector.tags_list.item(1).text() == (
        "Unknown WordPress tag (ID 99)"
    )
    assert (
        selector.tags_list.item(1).checkState()
        == Qt.CheckState.Checked
    )


def test_remote_tag_selector_replaces_unknown_name_when_loaded(
    qtbot,
) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    selector.set_selected_ids((99,))
    selector.set_available_tags((
        RemoteTag(remote_id=99, name="Announcements"),
    ))

    assert selector.tags_list.count() == 1
    assert selector.tags_list.item(0).text() == "Announcements"
    assert selector.selected_ids() == (99,)


def test_remote_tag_selector_does_not_emit_during_programmatic_setup(
    qtbot,
) -> None:
    selector = RemoteTagSelector()
    qtbot.addWidget(selector)

    changed = Mock()
    selector.selection_changed.connect(changed)

    selector.set_selected_ids((12,))
    selector.set_available_tags((
        RemoteTag(remote_id=12, name="Python"),
    ))

    changed.assert_not_called()
    assert selector.selected_ids() == (12,)
