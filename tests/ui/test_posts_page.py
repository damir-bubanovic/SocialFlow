from PySide6.QtWidgets import QWidget
from socialflow.ui.posts.post_editor import PostEditor

from socialflow.ui.posts.posts_page import PostsPage
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


def test_posts_page_is_widget(qtbot) -> None:
    page = PostsPage()
    qtbot.addWidget(page)

    assert isinstance(page, QWidget)

def test_posts_page_contains_post_editor(qtbot) -> None:
    page = PostsPage()
    qtbot.addWidget(page)

    assert isinstance(page.post_editor, PostEditor)

def test_posts_page_forwards_publish_request(qtbot) -> None:
    page = PostsPage()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")

    with qtbot.waitSignal(page.publish_requested) as blocker:
        page.post_editor.publish_button.click()

    post = blocker.args[0]

    assert isinstance(post, Post)
    assert post.text == "Hello from SocialFlow"
    assert post.language == Language.CROATIAN