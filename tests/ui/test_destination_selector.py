from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.destination_selector import DestinationSelector


def test_destination_selector_has_expected_destinations(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    assert selector.facebook.text() == "Facebook"
    assert selector.instagram.text() == "Instagram"
    assert selector.wordpress.text() == "WordPress"


def test_no_destinations_are_selected_by_default(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    assert selector.selected_destinations() == ()


def test_selected_destinations_are_returned(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    selector.facebook.setChecked(True)
    selector.wordpress.setChecked(True)

    assert selector.selected_destinations() == (
        PublishingDestination.FACEBOOK,
        PublishingDestination.WORDPRESS,
    )