from PySide6.QtWidgets import QVBoxLayout, QWidget
from socialflow.ui.navigation import Navigation
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.application.publishing.null_publisher import NullPublisher
from socialflow.application.publishing.publish_post import PublishPost


class MainContent(QWidget):
    """Primary content area of the SocialFlow main window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.navigation = Navigation(self)
        publisher = NullPublisher()
        publish_post = PublishPost(publisher)

        self.posts_page = PostsPage(
            publish_post=publish_post,
            parent=self,
        )

        layout = QVBoxLayout()
        layout.addWidget(self.navigation)
        layout.addWidget(self.posts_page)

        self.setLayout(layout)