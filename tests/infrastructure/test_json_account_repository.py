import json
import pytest

from socialflow.infrastructure.accounts.errors import AccountStorageError
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.json_account_repository import (
    JsonAccountRepository,
)


def test_json_account_repository_is_empty_when_file_does_not_exist(
    tmp_path,
) -> None:
    repository = JsonAccountRepository(
        tmp_path / "accounts.json"
    )

    assert repository.all() == ()


def test_json_account_repository_persists_account(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(account)

    reloaded_repository = JsonAccountRepository(file_path)

    assert reloaded_repository.all() == (account,)


def test_json_account_repository_preserves_unicode(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    account = Account(
        name="Društvena mreža čćžšđ",
        destination=PublishingDestination.INSTAGRAM,
    )

    repository.add(account)

    reloaded_repository = JsonAccountRepository(file_path)

    assert reloaded_repository.all() == (account,)


def test_json_account_repository_removes_account(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(account)
    repository.remove(account)

    assert repository.all() == ()


def test_json_account_repository_updates_account(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    current = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    updated = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(current)
    repository.update(current, updated)

    assert repository.all() == (updated,)


def test_json_account_repository_writes_readable_utf8_json(
    tmp_path,
) -> None:
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    repository.add(
        Account(
            name="Čakovec društvena mreža",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == [
        {
            "name": "Čakovec društvena mreža",
            "destination": "facebook",
        }
    ]

def test_json_account_repository_rejects_invalid_json(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"
    file_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    repository = JsonAccountRepository(file_path)

    with pytest.raises(
        AccountStorageError,
        match="Account storage contains invalid data.",
    ):
        repository.all()


def test_json_account_repository_rejects_missing_account_fields(
    tmp_path,
) -> None:
    file_path = tmp_path / "accounts.json"
    file_path.write_text(
        '[{"name": "SocialFlow Facebook"}]',
        encoding="utf-8",
    )

    repository = JsonAccountRepository(file_path)

    with pytest.raises(
        AccountStorageError,
        match="Account storage contains invalid data.",
    ):
        repository.all()


def test_json_account_repository_rejects_unknown_destination(
    tmp_path,
) -> None:
    file_path = tmp_path / "accounts.json"
    file_path.write_text(
        '[{"name": "SocialFlow", "destination": "unknown"}]',
        encoding="utf-8",
    )

    repository = JsonAccountRepository(file_path)

    with pytest.raises(
        AccountStorageError,
        match="Account storage contains invalid data.",
    ):
        repository.all()