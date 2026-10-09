import json
import pytest

from socialflow.infrastructure.accounts.errors import AccountStorageError
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.infrastructure.publishing.json_publication_repository import (
    JsonPublicationRepository,
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

    account = Account(
        name="Čakovec društvena mreža",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(account)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == [
        {
            "id": str(account.id),
            "name": "Čakovec društvena mreža",
            "destination": "facebook",
        }
    ]

    content = file_path.read_text(encoding="utf-8")

    assert "Čakovec društvena mreža" in content
    assert "\\u010c" not in content

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

def test_repository_migrates_legacy_accounts_without_ids(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"

    legacy_accounts = [
        {
            "name": "Glavna Facebook stranica",
            "destination": "facebook",
        },
        {
            "name": "Instagram čćžšđ",
            "destination": "instagram",
        },
    ]

    file_path.write_text(
        json.dumps(legacy_accounts, ensure_ascii=False),
        encoding="utf-8",
    )

    repository = JsonAccountRepository(file_path)

    accounts = repository.all()

    assert len(accounts) == 2
    assert accounts[0].id != accounts[1].id
    assert accounts[0].name == "Glavna Facebook stranica"
    assert accounts[1].name == "Instagram čćžšđ"

    stored = json.loads(file_path.read_text(encoding="utf-8"))

    assert stored[0]["id"] == str(accounts[0].id)
    assert stored[1]["id"] == str(accounts[1].id)


def test_repository_preserves_migrated_ids_across_loads(tmp_path) -> None:
    file_path = tmp_path / "accounts.json"

    file_path.write_text(
        json.dumps([
            {
                "name": "Main Facebook",
                "destination": "facebook",
            }
        ]),
        encoding="utf-8",
    )

    first_repository = JsonAccountRepository(file_path)
    first_account = first_repository.all()[0]

    second_repository = JsonAccountRepository(file_path)
    second_account = second_repository.all()[0]

    assert first_account.id == second_account.id
    assert first_account == second_account

def test_repository_migrates_legacy_publication_account_id(
    tmp_path,
) -> None:
    from socialflow.infrastructure.accounts.json_account_repository import (
        JsonAccountRepository,
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        tmp_path / "accounts.json"
    )
    account_repository.add(account)

    file_path = tmp_path / "publications.json"

    legacy_data = [
        {
            "id": "12345678-1234-5678-1234-567812345678",
            "account": {
                "name": "Main Facebook",
                "destination": "facebook",
            },
            "post": {
                "text": "Legacy publication",
                "language": "EN",
            },
            "published_at": "2026-10-05T21:30:00",
        }
    ]

    file_path.write_text(
        json.dumps(legacy_data),
        encoding="utf-8",
    )

    repository = JsonPublicationRepository(
        file_path,
        account_repository=account_repository,
    )

    history = repository.recent_for_account(account)

    assert len(history) == 1
    assert history[0].account.id == account.id

    stored = json.loads(file_path.read_text(encoding="utf-8"))

    assert stored[0]["account"]["id"] == str(account.id)