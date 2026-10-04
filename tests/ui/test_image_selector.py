from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QWidget,
)

from socialflow.ui.posts.image_selector import ImageSelector


def create_test_image(
    path: Path,
    width: int = 200,
    height: int = 100,
) -> None:
    """Create a real image file for image-selector tests."""
    pixmap = QPixmap(width, height)
    assert pixmap.save(str(path))


def test_image_selector_is_widget(qtbot) -> None:
    selector = ImageSelector()
    qtbot.addWidget(selector)

    assert isinstance(selector, QWidget)


def test_image_selector_starts_without_images(qtbot) -> None:
    selector = ImageSelector()
    qtbot.addWidget(selector)

    assert selector.selected_images() == ()
    assert selector.status_label.text() == "No images selected."


def test_image_selector_selects_images(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    selector = ImageSelector()
    qtbot.addWidget(selector)

    first_image = tmp_path / "socialflow-first.jpg"
    second_image = tmp_path / "socialflow-second.png"

    create_test_image(first_image)
    create_test_image(second_image)

    image_paths = (
        str(first_image),
        str(second_image),
    )

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (list(image_paths), ""),
    )

    selector.select_button.click()

    assert tuple(
        image.path for image in selector.selected_images()
    ) == (
        first_image,
        second_image,
    )

    assert selector.status_label.text() == "2 image(s) selected."
    assert selector.filenames_label.text() == (
        "socialflow-first.jpg\n"
        "socialflow-second.png"
    )


def test_image_selector_keeps_selection_when_dialog_is_cancelled(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    selector = ImageSelector()
    qtbot.addWidget(selector)

    image_path = tmp_path / "socialflow-image.jpg"
    create_test_image(image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector.select_button.click()

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([], ""),
    )

    selector.select_button.click()

    assert len(selector.selected_images()) == 1
    assert selector.selected_images()[0].path == image_path


def test_image_selector_can_clear_selected_images(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    selector = ImageSelector()
    qtbot.addWidget(selector)

    image_path = tmp_path / "socialflow-image.jpg"
    create_test_image(image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector.select_button.click()

    assert len(selector.selected_images()) == 1

    selector.clear_button.click()

    assert selector.selected_images() == ()
    assert selector.status_label.text() == "No images selected."
    assert selector.filenames_label.text() == ""


def test_image_selector_displays_image_preview(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "socialflow-image.png"
    create_test_image(image_path)

    selector = ImageSelector()
    qtbot.addWidget(selector)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector.select_button.click()

    assert selector.preview_layout.count() == 1

    preview_container = selector.preview_layout.itemAt(0).widget()

    assert preview_container is not None

    preview = preview_container.findChild(QLabel)

    assert preview is not None
    assert preview.pixmap() is not None
    assert not preview.pixmap().isNull()


def test_image_selector_appends_images_from_multiple_selections(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_image = tmp_path / "first.jpg"
    second_image = tmp_path / "second.png"

    create_test_image(first_image)
    create_test_image(second_image)

    selections = iter([
        ([str(first_image)], ""),
        ([str(second_image)], ""),
    ])

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: next(selections),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()
    selector.select_button.click()

    assert tuple(
        image.path for image in selector.selected_images()
    ) == (
        first_image,
        second_image,
    )


def test_image_selector_does_not_add_duplicate_images(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "socialflow-image.jpg"
    create_test_image(image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()
    selector.select_button.click()

    assert len(selector.selected_images()) == 1
    assert selector.selected_images()[0].path == image_path


def test_image_selector_can_remove_one_selected_image(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_image = tmp_path / "first.jpg"
    second_image = tmp_path / "second.png"

    create_test_image(first_image)
    create_test_image(second_image)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (
            [str(first_image), str(second_image)],
            "",
        ),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()

    assert selector.preview_layout.count() == 2

    image_to_remove = selector.selected_images()[0]
    selector.remove_image(image_to_remove)

    assert tuple(
        image.path for image in selector.selected_images()
    ) == (second_image,)

    assert selector.status_label.text() == "1 image(s) selected."
    assert selector.filenames_label.text() == "second.png"
    assert selector.preview_layout.count() == 1


def test_image_preview_remove_button_removes_image(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "socialflow-image.png"
    create_test_image(image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()

    assert len(selector.selected_images()) == 1
    assert selector.preview_layout.count() == 1

    preview_container = selector.preview_layout.itemAt(0).widget()

    assert preview_container is not None

    remove_button = preview_container.findChild(QPushButton)

    assert remove_button is not None

    remove_button.click()

    assert selector.selected_images() == ()
    assert selector.status_label.text() == "No images selected."
    assert selector.filenames_label.text() == ""
    assert selector.preview_layout.count() == 0


def test_image_selector_rejects_unreadable_image(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "invalid-image.jpg"
    image_path.write_text("This is not actually an image.")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(image_path)], ""),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()

    assert selector.selected_images() == ()
    assert selector.status_label.text() == "No images selected."
    assert "Unreadable image file" in selector.error_label.text()

def test_image_selector_keeps_valid_images_when_one_is_unreadable(
    qtbot,
    monkeypatch,
    tmp_path: Path,
) -> None:
    valid_image = tmp_path / "valid-image.png"
    invalid_image = tmp_path / "invalid-image.jpg"

    create_test_image(valid_image)
    invalid_image.write_text("This is not actually an image.")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (
            [str(valid_image), str(invalid_image)],
            "",
        ),
    )

    selector = ImageSelector()
    qtbot.addWidget(selector)

    selector.select_button.click()

    assert tuple(
        image.path for image in selector.selected_images()
    ) == (valid_image,)

    assert selector.status_label.text() == "1 image(s) selected."
    assert selector.filenames_label.text() == "valid-image.png"
    assert selector.preview_layout.count() == 1
    assert "Unreadable image file" in selector.error_label.text()