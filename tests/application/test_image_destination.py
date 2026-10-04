from socialflow.application.images.image_destination import ImageDestination


def test_image_destinations_have_stable_values() -> None:
    assert ImageDestination.FACEBOOK == "facebook"
    assert ImageDestination.INSTAGRAM == "instagram"
    assert ImageDestination.WORDPRESS == "wordpress"