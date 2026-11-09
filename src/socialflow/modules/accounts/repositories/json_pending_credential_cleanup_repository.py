import json
import os
import tempfile
from pathlib import Path
from uuid import UUID


class JsonPendingCredentialCleanupRepository:
    """Persist credential cleanup requests without storing secrets."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def all(self) -> tuple[str, ...]:
        if not self._file_path.exists():
            return ()

        try:
            data = json.loads(
                self._file_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ValueError("Invalid credential cleanup journal.") from exc

        if not isinstance(data, list):
            raise ValueError("Invalid credential cleanup journal.")

        if not all(
            isinstance(key, str) and self._is_valid_key(key)
            for key in data
        ):
            raise ValueError("Invalid credential cleanup journal.")

        if len(data) != len(set(data)):
            raise ValueError("Duplicate credential cleanup entries.")

        return tuple(data)

    def add(self, key: str) -> None:
        if not self._is_valid_key(key):
            raise ValueError("Invalid credential cleanup key.")

        pending = list(self.all())

        if key in pending:
            return

        pending.append(key)
        self._save(pending)

    def remove(self, key: str) -> None:
        pending = list(self.all())

        if key not in pending:
            return

        pending.remove(key)
        self._save(pending)

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        if not isinstance(key, str):
            return False

        parts = key.split(":")

        if len(parts) != 3:
            return False

        platform, account_id, credential_type = parts

        expected_types = {
            "facebook": "page_access_token",
            "wordpress": "application_password",
        }

        if expected_types.get(platform) != credential_type:
            return False

        try:
            parsed_id = UUID(account_id)
        except (ValueError, AttributeError):
            return False

        return str(parsed_id) == account_id

    def _save(self, pending: list[str]) -> None:
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        content = json.dumps(
            pending,
            ensure_ascii=False,
            indent=2,
        )

        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self._file_path.name}.",
            suffix=".tmp",
            dir=self._file_path.parent,
        )

        try:
            try:
                with os.fdopen(
                    descriptor,
                    "w",
                    encoding="utf-8",
                ) as temporary_file:
                    temporary_file.write(content)
            except BaseException:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                raise

            os.replace(
                temporary_path,
                self._file_path,
            )
        finally:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass