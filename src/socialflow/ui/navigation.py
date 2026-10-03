from PySide6.QtWidgets import QTabBar, QVBoxLayout, QWidget


class Navigation(QWidget):
    """Primary navigation for SocialFlow."""

    POSTS_INDEX = 0
    ACCOUNTS_INDEX = 1
    SETTINGS_INDEX = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.tab_bar = QTabBar(self)
        self.tab_bar.addTab("Posts")
        self.tab_bar.addTab("Accounts")
        self.tab_bar.addTab("Settings")

        layout = QVBoxLayout()
        layout.addWidget(self.tab_bar)

        self.setLayout(layout)