from socialflow.application.images.image_destination import ImageDestination
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile


DEFAULT_IMAGE_PROFILES: dict[ImageDestination, ImageProfile] = {
    ImageDestination.INSTAGRAM: ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=1080,
            height=1350,
        ),
        output_format="JPEG",
    ),
}