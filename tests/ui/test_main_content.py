from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.ui.main_content import MainContent


def test_main_content_is_widget(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content, QWidget)

def test_main_content_uses_vertical_layout(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.layout(), QVBoxLayout)