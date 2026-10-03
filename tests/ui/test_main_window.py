from PySide6.QtWidgets import QMainWindow

from socialflow.ui.main_content import MainContent

from socialflow.ui.main_window import MainWindow


def test_main_window_is_qt_main_window(qtbot) -> None:
    window = MainWindow()

    qtbot.addWidget(window)

    assert isinstance(window, QMainWindow)


def test_main_window_has_socialflow_title(qtbot) -> None:
    window = MainWindow()

    qtbot.addWidget(window)

    assert window.windowTitle() == "SocialFlow"

def test_main_window_has_initial_size(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.width() == 1200
    assert window.height() == 800

def test_main_window_has_central_widget(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert isinstance(window.centralWidget(), MainContent)