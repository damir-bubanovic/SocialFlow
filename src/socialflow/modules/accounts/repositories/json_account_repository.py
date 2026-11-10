import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from socialflow.modules.accounts.models.account_id import AccountId
from socialflow.modules.accounts.repositories.account_repository import AccountRepository
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.repositories.account_serializer import (
    AccountSerializer,
)
from socialflow.modules.accounts.repositories.errors import AccountStorageError


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
                        wordpress_config=account.wordpress_config,
                        facebook_config=account.facebook_config,
                        instagram_config=account.instagram_config,
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

        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self._file_path.name}.",
            suffix=".tmp",
            dir=self._file_path.parent,
        )

        try:
            try:
                with os.fdopen(
                        file_descriptor,
                        "w",
                        encoding="utf-8",
                ) as temporary_file:
                    temporary_file.write(content)
            except BaseException:
                # fdopen() may fail before taking ownership of the descriptor.
                try:
                    os.close(file_descriptor)
                except OSError:
                    pass
                raise

            os.replace(
                temporary_path,
                self._file_path,
            )
        finally:
            # After successful replacement the temporary path no longer exists.
            # After failure, remove any remaining temporary file.
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass