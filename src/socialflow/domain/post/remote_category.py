from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoteCategory:
    """A WordPress category with an optional parent category."""

    remote_id: int
    name: str
    parent_id: int = 0

    def __post_init__(self) -> None:
        if type(self.remote_id) is not int or self.remote_id <= 0:
            raise ValueError(
                "Remote category ID must be a positive integer."
            )

        if not isinstance(self.name, str):
            raise ValueError(
                "Remote category name must be a non-empty string."
            )

        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Remote category name cannot be empty."
            )

        if type(self.parent_id) is not int or self.parent_id < 0:
            raise ValueError(
                "Parent category ID must be a non-negative integer."
            )

        if self.parent_id == self.remote_id:
            raise ValueError(
                "A category cannot be its own parent."
            )

        object.__setattr__(self, "name", normalized_name)