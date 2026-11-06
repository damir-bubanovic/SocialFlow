
"""Tests for Facebook multipart request encoding."""
from unittest.mock import patch
import pytest
from typing import Any

from socialflow.modules.facebook.api.facebook_multipart_encoder import (
    MAX_MULTIPART_SIZE,
    FacebookMultipartEncoder,
)


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("photo.jpg", "image/jpeg"),
        ("photo.jpeg", "image/jpeg"),
        ("photo.png", "image/png"),
        ("PHOTO.JPG", "image/jpeg"),
    ],
)
def test_encodes_supported_images(
    filename: str,
    mime_type: str,
) -> None:
    payload = FacebookMultipartEncoder.encode(
        fields={"message": "Hello Facebook"},
        filename=filename,
        image_data=b"\x00\x01\x02",
    )

    boundary = payload.content_type.split("boundary=", 1)[1]

    assert payload.content_type.startswith("multipart/form-data;")
    assert f"--{boundary}\r\n".encode() in payload.body
    assert f"filename=\"{filename}\"".encode() in payload.body
    assert f"Content-Type: {mime_type}".encode() in payload.body
    assert b"Hello Facebook" in payload.body
    assert b"\x00\x01\x02" in payload.body
    assert payload.body.endswith(
        f"--{boundary}--\r\n".encode()
    )


def test_encodes_unicode_text() -> None:
    payload = FacebookMultipartEncoder.encode(
        fields={"message": "Pozdrav svijete"},
        filename="photo.png",
        image_data=b"image-data",
    )

    assert "Pozdrav svijete".encode("utf-8") in payload.body


def test_generates_unique_boundaries() -> None:
    first = FacebookMultipartEncoder.encode(
        fields={},
        filename="photo.jpg",
        image_data=b"data",
    )
    second = FacebookMultipartEncoder.encode(
        fields={},
        filename="photo.jpg",
        image_data=b"data",
    )

    assert first.content_type != second.content_type


@pytest.mark.parametrize(
    "filename",
    [
        "../photo.jpg",
        "folder/photo.jpg",
        "photo.webp",
        'photo".jpg',
        "photo\r\n.jpg",
        "",
    ],
)
def test_rejects_invalid_filenames(filename: str) -> None:
    with pytest.raises(ValueError):
        FacebookMultipartEncoder.encode(
            fields={},
            filename=filename,
            image_data=b"data",
        )


@pytest.mark.parametrize(
    "fields",
    [
        {"bad name": "value"},
        {"bad\r\nname": "value"},
        {"source": "duplicate"},
        {"message": 123},
    ],
)
def test_rejects_invalid_fields(fields: dict) -> None:
    with pytest.raises(ValueError):
        FacebookMultipartEncoder.encode(
            fields=fields,
            filename="photo.jpg",
            image_data=b"data",
        )


@pytest.mark.parametrize("image_data", [b"", "not bytes", None])
def test_rejects_invalid_image_data(image_data: Any) -> None:
    with pytest.raises(ValueError):
        FacebookMultipartEncoder.encode(
            fields={},
            filename="photo.jpg",
            image_data=image_data,
        )


def test_rejects_oversized_image() -> None:
    with pytest.raises(ValueError, match="size limit"):
        FacebookMultipartEncoder.encode(
            fields={},
            filename="photo.jpg",
            image_data=b"x" * (MAX_MULTIPART_SIZE + 1),
        )


def test_rejects_oversized_encoded_body() -> None:
    with pytest.raises(ValueError, match="size limit"):
        FacebookMultipartEncoder.encode(
            fields={"message": "x" * MAX_MULTIPART_SIZE},
            filename="photo.jpg",
            image_data=b"x",
        )


@pytest.mark.parametrize(
    "filename",
    [
        "photo\n.jpg",
        "photo\r.jpg",
        "photo\t.jpg",
        "photo;.jpg",
        "photo=.jpg",
        "photo\\.jpg",
        "folder\\photo.jpg",
        ".hidden.jpg",
        "photo name.jpg",
    ],
)
def test_rejects_unsafe_filename_characters(
    filename: str,
) -> None:
    with pytest.raises(ValueError, match="filename"):
        FacebookMultipartEncoder.encode(
            fields={},
            filename=filename,
            image_data=b"image-data",
        )


def test_regenerates_boundary_if_present_in_image() -> None:
    first_token = "a" * 32
    second_token = "b" * 32

    image_data = (
        b"image-start--socialflow-"
        + first_token.encode("ascii")
        + b"--image-end"
    )

    with patch(
        "socialflow.modules.facebook.api."
        "facebook_multipart_encoder.secrets.token_hex",
        side_effect=[first_token, second_token],
    ) as token_generator:
        payload = FacebookMultipartEncoder.encode(
            fields={},
            filename="photo.jpg",
            image_data=image_data,
        )

    assert token_generator.call_count == 2
    assert payload.content_type.endswith(
        f"boundary=socialflow-{second_token}"
    )
    assert image_data in payload.body


def test_regenerates_boundary_if_present_in_text() -> None:
    first_token = "a" * 32
    second_token = "b" * 32

    message = f"Example --socialflow-{first_token} content"

    with patch(
        "socialflow.modules.facebook.api."
        "facebook_multipart_encoder.secrets.token_hex",
        side_effect=[first_token, second_token],
    ) as token_generator:
        payload = FacebookMultipartEncoder.encode(
            fields={"caption": message},
            filename="photo.jpg",
            image_data=b"image-data",
        )

    assert token_generator.call_count == 2
    assert payload.content_type.endswith(
        f"boundary=socialflow-{second_token}"
    )
    assert message.encode("utf-8") in payload.body


def test_rejects_repeated_boundary_collisions() -> None:
    token = "a" * 32
    image_data = f"--socialflow-{token}".encode("ascii")

    with patch(
        "socialflow.modules.facebook.api."
        "facebook_multipart_encoder.secrets.token_hex",
        return_value=token,
    ) as token_generator:
        with pytest.raises(
            ValueError,
            match="safe multipart boundary",
        ):
            FacebookMultipartEncoder.encode(
                fields={},
                filename="photo.jpg",
                image_data=image_data,
            )

    assert token_generator.call_count == 10


def test_rejects_header_injection_in_file_field() -> None:
    with pytest.raises(ValueError, match="field name"):
        FacebookMultipartEncoder.encode(
            fields={},
            filename="photo.jpg",
            image_data=b"image-data",
            file_field='source"\r\nX-Injected: yes',
        )


def test_allows_line_breaks_in_caption_content() -> None:
    caption = "First line\r\nSecond line"

    payload = FacebookMultipartEncoder.encode(
        fields={"caption": caption},
        filename="photo.jpg",
        image_data=b"image-data",
    )

    assert caption.encode("utf-8") in payload.body


def test_accepts_body_at_exact_size_limit() -> None:
    """An encoded request exactly at the limit is valid."""
    sample = FacebookMultipartEncoder.encode(
        fields={"caption": ""},
        filename="photo.jpg",
        image_data=b"x",
    )

    overhead = len(sample.body) - 1

    payload = FacebookMultipartEncoder.encode(
        fields={"caption": ""},
        filename="photo.jpg",
        image_data=b"x" * (MAX_MULTIPART_SIZE - overhead),
    )

    assert len(payload.body) == MAX_MULTIPART_SIZE


def test_rejects_body_one_byte_over_size_limit() -> None:
    """The encoded request, not just the image, is size-limited."""
    sample = FacebookMultipartEncoder.encode(
        fields={"caption": ""},
        filename="photo.jpg",
        image_data=b"x",
    )

    overhead = len(sample.body) - 1

    with pytest.raises(ValueError, match="size limit"):
        FacebookMultipartEncoder.encode(
            fields={"caption": ""},
            filename="photo.jpg",
            image_data=b"x" * (
                MAX_MULTIPART_SIZE - overhead + 1
            ),
        )
