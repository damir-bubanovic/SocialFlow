from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile
from socialflow.domain.publishing.destination import PublishingDestination


DEFAULT_IMAGE_PROFILES: dict[PublishingDestination, ImageProfile] = {
    PublishingDestination.FACEBOOK: ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=2048,
            height=2048,
        ),
        output_format="JPEG",
    ),
    PublishingDestination.INSTAGRAM: ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=1080,
            height=1350,
        ),
        output_format="JPEG",
        minimum_aspect_ratio=0.8,
        maximum_aspect_ratio=1.91,
    ),
    PublishingDestination.WORDPRESS: ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=2048,
            height=2048,
        ),
        output_format="JPEG",
    ),
}