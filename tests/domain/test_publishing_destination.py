from socialflow.domain.publishing.destination import PublishingDestination


def test_supported_publishing_destinations() -> None:
    assert str(PublishingDestination.FACEBOOK) == "facebook"
    assert str(PublishingDestination.INSTAGRAM) == "instagram"
    assert str(PublishingDestination.WORDPRESS) == "wordpress"

def test_publishing_destination_display_names() -> None:
    assert PublishingDestination.FACEBOOK.display_name == "Facebook"
    assert PublishingDestination.INSTAGRAM.display_name == "Instagram"
    assert PublishingDestination.WORDPRESS.display_name == "WordPress"