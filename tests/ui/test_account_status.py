from socialflow.ui.accounts.account_status import AccountStatus


def test_account_status_is_empty_by_default(qtbot) -> None:
    status = AccountStatus()
    qtbot.addWidget(status)

    assert status.text() == ""
    assert status.property("status") == ""


def test_account_status_can_show_success(qtbot) -> None:
    status = AccountStatus()
    qtbot.addWidget(status)

    status.show_success()

    assert status.text() == "Account added."
    assert status.property("status") == "success"


def test_account_status_can_show_error(qtbot) -> None:
    status = AccountStatus()
    qtbot.addWidget(status)

    status.show_error()

    assert status.text() == "Account could not be added."
    assert status.property("status") == "error"


def test_account_status_can_be_cleared(qtbot) -> None:
    status = AccountStatus()
    qtbot.addWidget(status)

    status.show_success()
    status.clear_status()

    assert status.text() == ""
    assert status.property("status") == ""