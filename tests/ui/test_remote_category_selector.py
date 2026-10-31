
from PySide6.QtCore import Qt

from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.ui.posts.remote_category_selector import (
    RemoteCategorySelector,
)


def sample_categories():
    return (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", parent_id=10),
        RemoteCategory(30, "JavaScript", parent_id=10),
        RemoteCategory(40, "Tutorials"),
    )


def item_by_id(selector, category_id):
    for index in range(selector.categories_list.count()):
        item = selector.categories_list.item(index)
        if item.data(Qt.ItemDataRole.UserRole) == category_id:
            return item

    raise AssertionError(
        f"Category {category_id} not found"
    )


def test_selector_starts_empty(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)

    assert selector.selected_ids() == ()
    assert selector.categories_list.count() == 0


def test_selector_displays_parent_and_child_categories(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)

    selector.set_available_categories(sample_categories())

    parent = item_by_id(selector, 10)
    child = item_by_id(selector, 20)

    assert parent.text() == "Technology"
    assert child.text().strip() == "Python"
    assert child.text().startswith("    ")


def test_selector_supports_multiple_categories(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_available_categories(sample_categories())

    item_by_id(selector, 10).setCheckState(
        Qt.CheckState.Checked
    )
    item_by_id(selector, 20).setCheckState(
        Qt.CheckState.Checked
    )

    assert selector.selected_ids() == (10, 20)


def test_selecting_child_does_not_select_parent(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_available_categories(sample_categories())

    item_by_id(selector, 20).setCheckState(
        Qt.CheckState.Checked
    )

    assert selector.selected_ids() == (20,)
    assert item_by_id(selector, 10).checkState() == (
        Qt.CheckState.Unchecked
    )


def test_unchecking_category_preserves_other_selections(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_available_categories(sample_categories())
    selector.set_selected_ids((10, 20))

    item_by_id(selector, 10).setCheckState(
        Qt.CheckState.Unchecked
    )

    assert selector.selected_ids() == (20,)


def test_refresh_preserves_selected_ids(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_available_categories(sample_categories())
    selector.set_selected_ids((20,))

    selector.set_available_categories(
        (
            RemoteCategory(10, "Technology"),
            RemoteCategory(20, "Python 3", parent_id=10),
        )
    )

    assert selector.selected_ids() == (20,)
    assert item_by_id(selector, 20).text().strip() == "Python 3"


def test_unknown_assigned_category_is_preserved(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_selected_ids((999,))
    selector.set_available_categories(sample_categories())

    assert selector.selected_ids() == (999,)
    assert "Unknown WordPress category" in (
        item_by_id(selector, 999).text()
    )


def test_duplicate_selected_ids_are_removed(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)

    selector.set_selected_ids((10, 10, 20, 20))

    assert selector.selected_ids() == (10, 20)


def test_selection_changed_emitted_for_user_change(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)
    selector.set_available_categories(sample_categories())

    with qtbot.waitSignal(
        selector.selection_changed,
        timeout=1000,
    ):
        item_by_id(selector, 20).setCheckState(
            Qt.CheckState.Checked
        )


def test_programmatic_refresh_does_not_emit_selection_changed(
    qtbot,
):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)

    emitted = []
    selector.selection_changed.connect(
        lambda: emitted.append(True)
    )

    selector.set_selected_ids((20,))
    selector.set_available_categories(sample_categories())

    assert emitted == []


def test_categories_are_sorted_hierarchically(qtbot):
    selector = RemoteCategorySelector()
    qtbot.addWidget(selector)

    selector.set_available_categories(
        (
            RemoteCategory(30, "Zebra", parent_id=10),
            RemoteCategory(40, "Tutorials"),
            RemoteCategory(10, "Technology"),
            RemoteCategory(20, "Alpha", parent_id=10),
        )
    )

    labels = [
        selector.categories_list.item(index).text().strip()
        for index in range(selector.categories_list.count())
    ]

    assert labels == [
        "Tutorials",
        "Technology",
        "Alpha",
        "Zebra",
    ]
