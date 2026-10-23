
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoteTag:
    """A tag identified by its remote platform ID."""

    remote_id: int
    name: str

    def __post_init__(self) -> None:
        if type(self.remote_id) is not int or self.remote_id <= 0:
            raise ValueError(
                "Remote tag ID must be a positive integer."
            )

        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Remote tag name cannot be empty."
            )

        object.__setattr__(self, "name", normalized_name)
