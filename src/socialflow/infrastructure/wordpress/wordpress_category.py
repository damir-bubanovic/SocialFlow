
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordPressCategory:
    """A category returned by the WordPress REST API."""

    id: int
    name: str
    parent_id: int = 0

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id <= 0:
            raise ValueError(
                "WordPress category ID must be a positive integer."
            )

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "WordPress category name must be a non-empty string."
            )

        if type(self.parent_id) is not int or self.parent_id < 0:
            raise ValueError(
                "WordPress parent category ID must be non-negative."
            )

        if self.parent_id == self.id:
            raise ValueError(
                "A WordPress category cannot be its own parent."
            )

        object.__setattr__(self, "name", self.name.strip())
