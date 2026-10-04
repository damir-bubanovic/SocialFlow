from pathlib import Path

from socialflow.infrastructure.storage.app_paths import AppPaths


def test_app_paths_provides_accounts_file() -> None:
    data_directory = Path("/tmp/socialflow")
    paths = AppPaths(data_directory)

    assert (
        paths.accounts_file
        == Path("/tmp/socialflow/accounts.json")
    )