from PySide6.QtWidgets import QApplication

from socialflow.main import create_application, run
from socialflow.ui.main_window import MainWindow


def test_create_application_creates_main_window(qtbot) -> None:
    application = QApplication.instance()

    window = create_application()

    qtbot.addWidget(window)

    assert application is not None
    assert application.applicationName() == "SocialFlow"
    assert application.organizationName() == "SocialFlow"
    assert isinstance(window, MainWindow)

def test_run_shows_main_window(monkeypatch, qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        "socialflow.main.create_application",
        lambda: window,
    )

    exit_code = run(start_event_loop=False)

    assert window.isVisible()
    assert exit_code == 0