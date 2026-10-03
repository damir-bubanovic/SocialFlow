from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


def test_post_contains_text_and_language() -> None:
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    assert post.text == "Hello from SocialFlow"
    assert post.language == Language.ENGLISH

def test_post_has_content_when_text_is_present() -> None:
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    assert post.has_content()


def test_post_has_no_content_when_text_is_empty() -> None:
    post = Post(
        text="   ",
        language=Language.CROATIAN,
    )

    assert not post.has_content()