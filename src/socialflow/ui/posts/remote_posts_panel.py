from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_post import RemotePost


class RemotePostsPanel(QWidget):
    """Display posts retrieved from a remote publishing platform."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title = QLabel("Remote WordPress posts", self)
        self.status_label = QLabel(self)
        self.posts_list = QListWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.posts_list)

        self.show_empty()

    def show_loading(self) -> None:
        """Display a loading indicator."""
        self.posts_list.clear()
        self.status_label.setText("Loading WordPress posts...")

    def show_posts(self, posts: tuple[RemotePost, ...]) -> None:
        """Display the retrieved remote posts."""
        self.posts_list.clear()

        for post in posts:
            preview = " ".join(post.content.split())
            preview = preview[:100]

            self.posts_list.addItem(
                f"{post.published_at:%Y-%m-%d} | "
                f"{post.status} | {preview}"
            )

        self.status_label.setText(
            f"{len(posts)} remote posts loaded"
            if posts
            else "No remote posts found."
        )

    def show_error(self, message: str) -> None:
        """Display a retrieval error."""
        self.posts_list.clear()
        self.status_label.setText(
            f"Unable to load WordPress posts: {message}"
        )

    def show_empty(self) -> None:
        """Reset the panel."""
        self.posts_list.clear()
        self.status_label.setText(
            "Select a WordPress account to load remote posts."
        )