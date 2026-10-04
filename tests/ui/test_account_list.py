from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.accounts.account_list import AccountList


def test_account_list_is_empty_by_default(qtbot) -> None:
    account_list = AccountList()
    qtbot.addWidget(account_list)

    assert account_list.count() == 0


def test_account_list_displays_accounts(qtbot) -> None:
    account_list = AccountList()
    qtbot.addWidget(account_list)

    accounts = (
        Account(
            name="SocialFlow Facebook",
            destination=PublishingDestination.FACEBOOK,
        ),
        Account(
            name="SocialFlow WordPress",
            destination=PublishingDestination.WORDPRESS,
        ),
    )

    account_list.set_accounts(accounts)

    assert account_list.count() == 2
    assert account_list.item(0).text() == "SocialFlow Facebook - Facebook"
    assert account_list.item(1).text() == "SocialFlow WordPress - WordPress"


def test_account_list_replaces_existing_accounts(qtbot) -> None:
    account_list = AccountList()
    qtbot.addWidget(account_list)

    account_list.set_accounts(
        (
            Account(
                name="SocialFlow Facebook",
                destination=PublishingDestination.FACEBOOK,
            ),
        )
    )

    account_list.set_accounts(
        (
            Account(
                name="SocialFlow Instagram",
                destination=PublishingDestination.INSTAGRAM,
            ),
        )
    )

    assert account_list.count() == 1
    assert account_list.item(0).text() == "SocialFlow Instagram - Instagram"

def test_account_list_returns_selected_account(qtbot) -> None:
    account_list = AccountList()
    qtbot.addWidget(account_list)

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_list.set_accounts((account,))
    account_list.setCurrentRow(0)

    assert account_list.selected_account() == account


def test_account_list_returns_none_without_selection(qtbot) -> None:
    account_list = AccountList()
    qtbot.addWidget(account_list)

    assert account_list.selected_account() is None