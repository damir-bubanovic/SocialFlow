from pathlib import Path

from socialflow.application.images.prepared_image import PreparedImage
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.domain.language.language import Language
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination


def test_prepared_post_preserves_source_and_prepared_images(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.jpg"
    prepared_path = tmp_path / "prepared.jpg"

    source_path.touch()
    prepared_path.touch()

    attachment = ImageAttachment(
        path=source_path,
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
        images=(attachment,),
    )

    prepared_image = PreparedImage(
        source=attachment,
        destination=PublishingDestination.INSTAGRAM,
        path=prepared_path,
    )

    prepared_post = PreparedPost(
        source=post,
        images=(prepared_image,),
    )

    assert prepared_post.source is post
    assert prepared_post.images == (prepared_image,)

def test_prepared_post_can_have_no_prepared_images() -> None:
    post = Post(
        text="Text-only post",
        language=Language.ENGLISH,
    )

    prepared_post = PreparedPost(
        source=post,
    )

    assert prepared_post.source is post
    assert prepared_post.images == ()