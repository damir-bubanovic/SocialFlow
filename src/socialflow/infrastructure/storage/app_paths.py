from pathlib import Path


class AppPaths:
    """Provides paths used for SocialFlow application data."""

    def __init__(self, data_directory: Path) -> None:
        self._data_directory = data_directory

    @property
    def accounts_file(self) -> Path:
        """Return the path to persistent account storage."""
        return self._data_directory / "accounts.json"

    @property
    def publications_file(self) -> Path:
        """Return the path to persistent publication history."""
        return self._data_directory / "publications.json"

    @property
    def prepared_images_directory(self) -> Path:
        """Return the directory for destination-prepared images."""
        return self._data_directory / "prepared_images"