import json
import os

import pytest

from socialflow.modules.accounts.repositories.errors import AccountStorageError
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.modules.posts.repositories.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
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

def test_failed_temporary_write_preserves_existing_accounts(
    tmp_path,
    monkeypatch,
) -> None:
    """A failed temporary write must not damage existing JSON."""
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    original = Account(
        name="Original Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(original)

    original_content = file_path.read_bytes()

    def fail_fdopen(*_args, **_kwargs):
        raise OSError("Simulated temporary write failure")

    new_account = Account(
        name="Second Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with monkeypatch.context() as patch:
        patch.setattr(os, "fdopen", fail_fdopen)

        with pytest.raises(
            OSError,
            match="Simulated temporary write failure",
        ):
            repository.add(new_account)

    assert file_path.read_bytes() == original_content
    assert repository.all() == (original,)

    # Temporary files must be cleaned up after failure.
    assert sorted(tmp_path.iterdir()) == [file_path]


def test_failed_atomic_replace_preserves_existing_accounts(
    tmp_path,
    monkeypatch,
) -> None:
    """Failed replacement must preserve the original account file."""
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    original = Account(
        name="Original Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(original)

    original_content = file_path.read_bytes()

    def fail_replace(_source, _destination):
        raise OSError("Simulated atomic replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)

    new_account = Account(
        name="Second Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(OSError, match="Simulated atomic replace failure"):
        repository.add(new_account)

    assert file_path.read_bytes() == original_content
    assert repository.all() == (original,)

    # Failed replacement must not leave temporary files behind.
    assert sorted(tmp_path.iterdir()) == [file_path]

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
    from socialflow.modules.accounts.repositories.json_account_repository import (
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


def test_json_account_repository_persists_wordpress_config(
    tmp_path,
) -> None:
    """WordPress settings survive reload without storing credentials."""
    file_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(file_path)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    repository.add(account)

    # Simulate restarting the application.
    reloaded_repository = JsonAccountRepository(file_path)
    restored_accounts = reloaded_repository.all()

    assert len(restored_accounts) == 1

    restored = restored_accounts[0]

    assert restored.id == account.id
    assert restored.name == "My WordPress"
    assert restored.destination == PublishingDestination.WORDPRESS
    assert restored.wordpress_config == account.wordpress_config

    # Inspect the actual JSON stored on disk.
    stored_data = json.loads(
        file_path.read_text(encoding="utf-8")
    )

    assert stored_data == [
        {
            "id": str(account.id),
            "name": "My WordPress",
            "destination": "wordpress",
            "wordpress_config": {
                "site_url": "https://example.com",
                "username": "admin",
            },
        }
    ]

    # Application passwords must never be persisted in JSON.
    assert "password" not in file_path.read_text(
        encoding="utf-8"
    ).lower()



def test_repository_persists_facebook_page_config(tmp_path) -> None:
    path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(path)

    account = Account(
        name="Facebook Test",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="SocialFlow Page",
        ),
    )

    repository.add(account)

    assert JsonAccountRepository(path).all() == (account,)

    stored = json.loads(path.read_text(encoding="utf-8"))

    assert stored[0]["facebook_config"] == {
        "page_id": "123456789",
        "page_name": "SocialFlow Page",
    }
    assert "access_token" not in stored[0]


def test_legacy_migration_preserves_facebook_config(tmp_path) -> None:
    path = tmp_path / "accounts.json"

    path.write_text(
        json.dumps([{
            "name": "Legacy Facebook",
            "destination": "facebook",
            "facebook_config": {
                "page_id": "123456789",
                "page_name": "Legacy Page",
            },
        }]),
        encoding="utf-8",
    )

    repository = JsonAccountRepository(path)
    first = repository.all()
    second = repository.all()

    assert first == second
    assert first[0].facebook_config == FacebookPageConfig(
        page_id="123456789",
        page_name="Legacy Page",
    )


def test_legacy_migration_preserves_wordpress_config(tmp_path) -> None:
    path = tmp_path / "accounts.json"

    path.write_text(
        json.dumps([{
            "name": "Legacy WordPress",
            "destination": "wordpress",
            "wordpress_config": {
                "site_url": "https://example.com",
                "username": "admin",
            },
        }]),
        encoding="utf-8",
    )

    restored = JsonAccountRepository(path).all()[0]

    assert restored.wordpress_config == WordPressConnectionConfig(
        site_url="https://example.com",
        username="admin",
    )


def test_repository_rejects_invalid_facebook_config(tmp_path) -> None:
    path = tmp_path / "accounts.json"

    path.write_text(
        json.dumps([{
            "name": "Invalid Facebook",
            "destination": "facebook",
            "facebook_config": {
                "page_name": "No Page ID",
            },
        }]),
        encoding="utf-8",
    )

    with pytest.raises(AccountStorageError):
        JsonAccountRepository(path).all()

def test_repository_persists_instagram_config(tmp_path) -> None:
    import json

    repository_path = tmp_path / "accounts.json"
    repository = JsonAccountRepository(repository_path)

    account = Account(
        name="Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="17841400000000000",
            username="socialflow_example",
        ),
    )

    repository.add(account)

    restored = JsonAccountRepository(repository_path).all()

    assert restored == (account,)

    stored = json.loads(repository_path.read_text(encoding="utf-8"))

    assert stored[0]["instagram_config"] == {
        "instagram_user_id": "17841400000000000",
        "username": "socialflow_example",
    }


def test_legacy_migration_preserves_instagram_config(tmp_path) -> None:
    import json

    repository_path = tmp_path / "accounts.json"
    repository_path.write_text(
        json.dumps(
            [
                {
                    "name": "Legacy Instagram",
                    "destination": "instagram",
                    "instagram_config": {
                        "instagram_user_id": "17841400000000000",
                        "username": "legacy_account",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    repository = JsonAccountRepository(repository_path)

    first = repository.all()
    second = repository.all()

    assert len(first) == 1
    assert first == second
    assert first[0].instagram_config == InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="legacy_account",
    )

    stored = json.loads(repository_path.read_text(encoding="utf-8"))

    assert stored[0]["id"] == str(first[0].id)
    assert stored[0]["instagram_config"] == {
        "instagram_user_id": "17841400000000000",
        "username": "legacy_account",
    }


def test_repository_rejects_invalid_instagram_config(tmp_path) -> None:
    import json

    import pytest

    from socialflow.modules.accounts.repositories.errors import (
        AccountStorageError,
    )

    repository_path = tmp_path / "accounts.json"
    repository_path.write_text(
        json.dumps(
            [
                {
                    "name": "Invalid Instagram",
                    "destination": "instagram",
                    "instagram_config": {
                        "username": "missing_user_id",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    repository = JsonAccountRepository(repository_path)

    with pytest.raises(AccountStorageError):
        repository.all()