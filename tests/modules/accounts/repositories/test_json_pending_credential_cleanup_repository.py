import json
import os

import pytest

from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)


def test_new_journal_is_empty(tmp_path) -> None:
    repository = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    assert repository.all() == ()


def test_journal_persists_pending_credential_key(tmp_path) -> None:
    path = tmp_path / "pending_credential_cleanup.json"
    repository = JsonPendingCredentialCleanupRepository(path)

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"

    repository.add(key)

    reloaded = JsonPendingCredentialCleanupRepository(path)

    assert reloaded.all() == (key,)


def test_journal_does_not_duplicate_pending_key(tmp_path) -> None:
    repository = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"

    repository.add(key)
    repository.add(key)

    assert repository.all() == (key,)


def test_journal_removes_completed_cleanup(tmp_path) -> None:
    repository = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"

    repository.add(key)
    repository.remove(key)

    assert repository.all() == ()


def test_journal_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "pending_credential_cleanup.json"
    path.write_text("{invalid json", encoding="utf-8")

    repository = JsonPendingCredentialCleanupRepository(path)

    with pytest.raises(ValueError):
        repository.all()


def test_journal_rejects_unknown_credential_key(tmp_path) -> None:
    path = tmp_path / "pending_credential_cleanup.json"
    path.write_text('["unknown:credential"]', encoding="utf-8")

    repository = JsonPendingCredentialCleanupRepository(path)

    with pytest.raises(ValueError):
        repository.all()

def test_failed_temporary_file_open_preserves_journal(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "pending_credential_cleanup.json"
    repository = JsonPendingCredentialCleanupRepository(path)

    original_key = (
        "facebook:12345678-1234-5678-1234-567812345678:page_access_token"
    )
    new_key = (
        "wordpress:87654321-4321-8765-4321-876543218765:application_password"
    )

    repository.add(original_key)
    original_content = path.read_bytes()

    def fail_fdopen(*_args, **_kwargs):
        raise OSError("Simulated temporary file open failure")

    with monkeypatch.context() as patch:
        patch.setattr(os, "fdopen", fail_fdopen)

        with pytest.raises(
            OSError,
            match="Simulated temporary file open failure",
        ):
            repository.add(new_key)

    assert path.read_bytes() == original_content
    assert repository.all() == (original_key,)
    assert sorted(tmp_path.iterdir()) == [path]


def test_failed_atomic_replace_preserves_journal(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "pending_credential_cleanup.json"
    repository = JsonPendingCredentialCleanupRepository(path)

    original_key = (
        "facebook:12345678-1234-5678-1234-567812345678:page_access_token"
    )
    new_key = (
        "wordpress:87654321-4321-8765-4321-876543218765:application_password"
    )

    repository.add(original_key)
    original_content = path.read_bytes()

    def fail_replace(_source, _destination):
        raise OSError("Simulated atomic replace failure")

    with monkeypatch.context() as patch:
        patch.setattr(os, "replace", fail_replace)

        with pytest.raises(
            OSError,
            match="Simulated atomic replace failure",
        ):
            repository.add(new_key)

    assert path.read_bytes() == original_content
    assert repository.all() == (original_key,)
    assert sorted(tmp_path.iterdir()) == [path]

@pytest.mark.parametrize(
    "invalid_data",
    [
        {},
        "facebook:12345678-1234-5678-1234-567812345678:page_access_token",
        [123],
        [None],
        ["unknown:12345678-1234-5678-1234-567812345678:token"],
        ["facebook:not-a-uuid:page_access_token"],
        ["facebook:12345678-1234-5678-1234-567812345678:wrong_type"],
        ["wordpress:12345678-1234-5678-1234-567812345678:page_access_token"],
        [
            "facebook:12345678-1234-5678-1234-567812345678:page_access_token",
            "facebook:12345678-1234-5678-1234-567812345678:page_access_token",
        ],
    ],
)
def test_journal_rejects_malformed_records(
    tmp_path,
    invalid_data,
) -> None:
    path = tmp_path / "pending_credential_cleanup.json"

    path.write_text(
        json.dumps(invalid_data),
        encoding="utf-8",
    )

    repository = JsonPendingCredentialCleanupRepository(path)

    with pytest.raises(ValueError):
        repository.all()