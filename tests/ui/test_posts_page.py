from PySide6.QtWidgets import QWidget

from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.post.post import Post
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.application.publishing.errors import PublishingError


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[Post] = []

    def publish(self, post: Post) -> None:
        self.published_posts.append(post)

class FailingPublisher(Publisher):
    """Test publisher that always fails."""

    def publish(self, post: Post) -> None:
        raise PublishingError("Publishing failed.")

def create_posts_page() -> PostsPage:
    publisher = RecordingPublisher()
    publish_post = PublishPost(publisher)

    return PostsPage(publish_post=publish_post)

def test_posts_page_is_widget(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page, QWidget)


def test_posts_page_contains_post_editor(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.post_editor, PostEditor)


def test_posts_page_delegates_publish_request(qtbot) -> None:
    publisher = RecordingPublisher()
    publish_post = PublishPost(publisher)
    page = PostsPage(publish_post=publish_post)
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.publish_button.click()

    assert len(publisher.published_posts) == 1
    assert publisher.published_posts[0].text == "Hello from SocialFlow"

def test_posts_page_contains_publish_status(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.publish_status, PublishStatus)


def test_posts_page_shows_status_after_publish(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Publish request completed."
    assert page.publish_status.property("status") == "success"

def test_posts_page_shows_error_when_publish_fails(qtbot) -> None:
    publisher = FailingPublisher()
    publish_post = PublishPost(publisher)
    page = PostsPage(publish_post=publish_post)
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Publish request failed."
    assert page.publish_status.property("status") == "error"