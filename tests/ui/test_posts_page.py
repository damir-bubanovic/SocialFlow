from PySide6.QtWidgets import QWidget

from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.post.post import Post
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.posts_page import PostsPage


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[Post] = []

    def publish(self, post: Post) -> None:
        self.published_posts.append(post)

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