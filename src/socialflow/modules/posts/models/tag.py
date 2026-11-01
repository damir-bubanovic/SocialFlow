from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tag:
    """A tag associated with a SocialFlow post."""

    name: str

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError("Tag name cannot be empty.")

        object.__setattr__(self, "name", normalized_name)