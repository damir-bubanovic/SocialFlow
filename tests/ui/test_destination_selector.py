from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.destination_selector import DestinationSelector


def test_destination_selector_is_empty_without_accounts(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    assert selector.selected_accounts() == ()


def test_destination_selector_displays_configured_accounts(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    instagram = Account(
        name="SocialFlow Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    selector.set_accounts(
        (
            facebook,
            instagram,
        )
    )

    assert selector._checkboxes[0].text() == "Main Facebook (Facebook)"
    assert (
        selector._checkboxes[1].text()
        == "SocialFlow Instagram (Instagram)"
    )


def test_destination_selector_returns_selected_accounts(qtbot) -> None:
    selector = DestinationSelector()
    qtbot.addWidget(selector)

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    selector.set_accounts(
        (
            facebook,
            wordpress,
        )
    )

    selector._checkboxes[0].setChecked(True)
    selector._checkboxes[1].setChecked(True)

    assert selector.selected_accounts() == (
        facebook,
        wordpress,
    )