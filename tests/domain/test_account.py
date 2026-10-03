from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


def test_account_contains_name_and_destination() -> None:
    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert account.name == "SocialFlow Facebook"
    assert account.destination == PublishingDestination.FACEBOOK

def test_account_has_name_when_name_is_present() -> None:
    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert account.has_name()


def test_account_has_no_name_when_name_is_whitespace() -> None:
    account = Account(
        name="   ",
        destination=PublishingDestination.FACEBOOK,
    )

    assert not account.has_name()

def test_account_can_be_normalized() -> None:
    account = Account(
        name="  SocialFlow Facebook  ",
        destination=PublishingDestination.FACEBOOK,
    )

    normalized = account.normalized()

    assert normalized.name == "SocialFlow Facebook"
    assert normalized.destination == PublishingDestination.FACEBOOK