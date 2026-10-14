from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordPressTag:
    """A tag returned by the WordPress REST API."""

    id: int
    name: str

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id <= 0:
            raise ValueError("WordPress tag ID must be a positive integer.")

        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError("WordPress tag name cannot be empty.")

        object.__setattr__(self, "name", normalized_name)