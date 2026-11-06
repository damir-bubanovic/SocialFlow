
"""Safe multipart/form-data encoding for Facebook uploads."""

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


MAX_MULTIPART_SIZE = 25 * 1024 * 1024

_FIELD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_FILENAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


@dataclass(frozen=True, slots=True)
class FacebookMultipartPayload:
    """Encoded multipart request body and content type."""

    body: bytes
    content_type: str


class FacebookMultipartEncoder:
    """Encode text fields and one image as multipart/form-data."""

    @staticmethod
    def encode(
        fields: Mapping[str, str],
        filename: str,
        image_data: bytes,
        file_field: str = "source",
    ) -> FacebookMultipartPayload:
        if not isinstance(fields, Mapping):
            raise ValueError("Multipart fields must be a mapping.")

        if not isinstance(filename, str) or not (
            _FILENAME_PATTERN.fullmatch(filename)
        ):
            raise ValueError("Invalid multipart filename.")

        if filename in {".", ".."}:
            raise ValueError("Invalid multipart filename.")

        extension = Path(filename).suffix.lower()

        if extension not in _CONTENT_TYPES:
            raise ValueError("Unsupported multipart image format.")

        if not isinstance(image_data, bytes) or not image_data:
            raise ValueError("Image data must be non-empty bytes.")

        if len(image_data) > MAX_MULTIPART_SIZE:
            raise ValueError("Multipart payload exceeds size limit.")

        def validate_field_name(field_name: str) -> None:
            if not isinstance(field_name, str) or not (
                _FIELD_PATTERN.fullmatch(field_name)
            ):
                raise ValueError("Invalid multipart field name.")

        validate_field_name(file_field)

        if file_field in fields:
            raise ValueError("Duplicate multipart file field.")

        for name, value in fields.items():
            validate_field_name(name)

            if not isinstance(value, str):
                raise ValueError(
                    "Multipart field values must be strings."
                )


        # Avoid multipart boundary collisions with supplied content.
        encoded_values = [
            value.encode("utf-8")
            for value in fields.values()
        ]

        for _ in range(10):
            boundary = f"socialflow-{secrets.token_hex(16)}"
            boundary_marker = f"--{boundary}".encode("ascii")

            if boundary_marker in image_data:
                continue

            if any(
                boundary_marker in value
                for value in encoded_values
            ):
                continue

            break
        else:
            raise ValueError(
                "Unable to generate a safe multipart boundary."
            )

        delimiter = f"--{boundary}\r\n".encode("ascii")


        parts: list[bytes] = []

        for name, value in fields.items():
            parts.append(
                delimiter
                + (
                    f'Content-Disposition: form-data; '
                    f'name="{name}"\r\n\r\n'
                ).encode("ascii")
                + value.encode("utf-8")
                + b"\r\n"
            )

        parts.append(
            delimiter
            + (
                f'Content-Disposition: form-data; '
                f'name="{file_field}"; '
                f'filename="{filename}"\r\n'
                f'Content-Type: {_CONTENT_TYPES[extension]}\r\n'
                f'\r\n'
            ).encode("ascii")
            + image_data
            + b"\r\n"
        )

        parts.append(
            f"--{boundary}--\r\n".encode("ascii")
        )

        body = b"".join(parts)

        if len(body) > MAX_MULTIPART_SIZE:
            raise ValueError("Multipart payload exceeds size limit.")

        return FacebookMultipartPayload(
            body=body,
            content_type=(
                f"multipart/form-data; boundary={boundary}"
            ),
        )
