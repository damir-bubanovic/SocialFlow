import json
from pathlib import Path
from uuid import uuid4

from socialflow.domain.account.account_id import AccountId
from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.domain.account.account import Account
from socialflow.infrastructure.accounts.account_serializer import (
    AccountSerializer,
)
from socialflow.infrastructure.accounts.errors import AccountStorageError


class JsonAccountRepository(AccountRepository):
    """Stores publishing accounts in a JSON file."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def all(self) -> tuple[Account, ...]:
        """Return all stored accounts."""
        if not self._file_path.exists():
            return ()

        try:
            content = self._file_path.read_text(encoding="utf-8")
            data = json.loads(content)

            accounts = []
            needs_migration = False

            for item in data:
                account = AccountSerializer.from_dict(item)

                if "id" not in item:
                    account = Account(
                        name=account.name,
                        destination=account.destination,
                        id=AccountId(uuid4()),
                    )
                    needs_migration = True

                accounts.append(account)

            if needs_migration:
                self._save(accounts)

            return tuple(accounts)
        except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
        ) as error:
            raise AccountStorageError(
                "Account storage contains invalid data."
            ) from error

    def add(self, account: Account) -> None:
        """Store an account."""
        accounts = list(self.all())
        accounts.append(account)
        self._save(accounts)

    def remove(self, account: Account) -> None:
        """Remove an account."""
        accounts = list(self.all())
        accounts.remove(account)
        self._save(accounts)

    def update(self, current: Account, updated: Account) -> None:
        """Replace an existing account."""
        accounts = list(self.all())

        index = accounts.index(current)
        accounts[index] = updated

        self._save(accounts)

    def _save(self, accounts: list[Account]) -> None:
        """Write accounts to the JSON file."""
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = [
            AccountSerializer.to_dict(account)
            for account in accounts
        ]

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )

        self._file_path.write_text(
            content,
            encoding="utf-8",
        )