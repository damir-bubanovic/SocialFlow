from pathlib import Path

from socialflow.domain.publishing.publication import Publication


class PublicationImageInspector:
    """Inspect stored publication image references."""

    @staticmethod
    def missing_images(
        image_paths: tuple[Path, ...],
    ) -> tuple[Path, ...]:
        """Return paths that no longer reference existing files."""
        return tuple(
            path
            for path in image_paths
            if not path.is_file()
        )