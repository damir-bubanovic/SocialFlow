from pathlib import Path

from socialflow.domain.language.language import Language
from socialflow.domain.post.image_attachment import ImageAttachment
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


def test_post_can_contain_image_attachments(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "socialflow-image.jpg"
    image_path.touch()

    image = ImageAttachment(path=image_path)

    post = Post(
        text="Post with an image",
        language=Language.ENGLISH,
        images=(image,),
    )

    assert post.images == (image,)


def test_post_with_image_has_content(tmp_path: Path) -> None:
    image_path = tmp_path / "image.jpg"
    image_path.touch()

    post = Post(
        text="",
        language=Language.ENGLISH,
        images=(
            ImageAttachment(path=image_path),
        ),
    )

    assert post.has_content()


def test_post_without_text_or_images_has_no_content() -> None:
    post = Post(
        text="",
        language=Language.ENGLISH,
        images=(),
    )

    assert not post.has_content()