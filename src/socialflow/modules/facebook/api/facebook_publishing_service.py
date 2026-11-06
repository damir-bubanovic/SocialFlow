
import json
from io import BytesIO

from PIL import Image, UnidentifiedImageError


from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_multipart_encoder import (
    MAX_MULTIPART_SIZE,
)
from socialflow.modules.facebook.services.facebook_image_validator import (
    FacebookImageValidator,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


class FacebookPublishingService:
    """Publish text posts and photos to a Facebook Page."""

    def __init__(
        self,
        client: FacebookGraphClient,
    ) -> None:
        if not isinstance(client, FacebookGraphClient):
            raise ValueError(
                "A Facebook Graph API client is required."
            )

        self._client = client

    def publish_photo(
        self,
        page_id: str,
        access_token: str,
        attachment: ImageAttachment,
        caption: str = "",
        published: bool = True,
    ) -> str:
        """Publish one Facebook Page photo and return its photo ID."""
        if not isinstance(page_id, str) or not page_id.strip():
            raise ValueError("A Facebook Page ID is required.")

        page_id = page_id.strip()

        if not page_id.isascii() or not page_id.isdecimal():
            raise ValueError("Invalid Facebook Page ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("A Facebook Page access token is required.")

        if not isinstance(attachment, ImageAttachment):
            raise ValueError("A valid image attachment is required.")


        if not isinstance(caption, str):
            raise ValueError("Facebook photo caption must be a string.")

        if not isinstance(published, bool):
            raise ValueError(
                "Facebook photo published flag must be a boolean."
            )

        path = FacebookImageValidator.validate(attachment)


        # Reject oversized files before reading their contents.
        try:
            if path.stat().st_size > MAX_MULTIPART_SIZE:
                raise ValueError(
                    "Facebook image exceeds the upload size limit."
                )
        except OSError:
            raise ValueError(
                "Facebook image file could not be read."
            ) from None

        # Read once, using a strict upper bound.
        try:
            with path.open("rb") as image_file:
                image_data = image_file.read(MAX_MULTIPART_SIZE + 1)
        except OSError:
            raise ValueError(
                "Facebook image file could not be read."
            ) from None

        if not image_data:
            raise ValueError("Facebook image file must not be empty.")

        if len(image_data) > MAX_MULTIPART_SIZE:
            raise ValueError(
                "Facebook image exceeds the upload size limit."
            )

        # Validate the exact bytes that will be uploaded.
        expected_formats = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
        }

        expected_format = expected_formats[path.suffix.lower()]

        try:
            with Image.open(BytesIO(image_data)) as image:
                actual_format = image.format
                image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
        ):
            raise ValueError(
                "Facebook image contains invalid or corrupted image data."
            ) from None

        if actual_format != expected_format:
            raise ValueError(
                "Facebook image content does not match its extension."
            )


        # Use a safe multipart filename, independent of the local path.
        upload_extension = (
            ".jpg" if expected_format == "JPEG" else ".png"
        )
        upload_filename = f"facebook-photo{upload_extension}"

        # The multipart encoder enforces the final encoded-body limit.
        response = self._client.post_multipart(
            path=f"{page_id}/photos",
            access_token=access_token,
            fields={
                "caption": caption,
                "published": "true" if published else "false",
            },
            filename=upload_filename,
            image_data=image_data,
        )


        photo_id = response.get("id")

        if not isinstance(photo_id, str) or not photo_id.strip():
            raise ValueError(
                "Facebook did not return a valid photo ID."
            )

        return photo_id.strip()


    def delete_unpublished_photo(
        self,
        photo_id: str,
        access_token: str,
    ) -> None:
        """Delete a Facebook photo uploaded during publishing."""

        if not isinstance(photo_id, str) or not photo_id:
            raise ValueError("A Facebook photo ID is required.")

        if not photo_id.isascii() or not photo_id.isdecimal():
            raise ValueError("Invalid Facebook photo ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError(
                "A Facebook Page access token is required."
            )

        response = self._client.delete(
            path=photo_id,
            access_token=access_token,
        )

        if response.get("success") is not True:
            raise ValueError(
                "Facebook did not confirm photo deletion."
            )

    def publish_text(
        self,
        page_id: str,
        access_token: str,
        message: str,
    ) -> str:
        """Publish a text post and return its Facebook post ID."""
        if not isinstance(page_id, str) or not page_id.strip():
            raise ValueError("A Facebook Page ID is required.")

        page_id = page_id.strip()

        if not page_id.isascii() or not page_id.isdecimal():
            raise ValueError("Invalid Facebook Page ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("A Facebook Page access token is required.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("A non-empty post message is required.")

        response = self._client.post(
            path=f"{page_id}/feed",
            access_token=access_token,
            params={"message": message},
        )

        post_id = response.get("id")

        if not isinstance(post_id, str) or not post_id.strip():
            raise ValueError(
                "Facebook did not return a valid post ID."
            )

        return post_id.strip()


    def publish_multiple_photos(
        self,
        page_id: str,
        access_token: str,
        attachments: tuple[ImageAttachment, ...],
        message: str = "",
    ) -> str:

        """Upload multiple photos and create one Facebook Page post."""

        if not isinstance(page_id, str) or not page_id.strip():
            raise ValueError("A Facebook Page ID is required.")

        page_id = page_id.strip()

        if not page_id.isascii() or not page_id.isdecimal():
            raise ValueError("Invalid Facebook Page ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError(
                "A Facebook Page access token is required."
            )


        if not isinstance(attachments, tuple) or len(attachments) < 2:
            raise ValueError(
                "At least two Facebook image attachments are required."
            )

        if len(attachments) > 10:
            raise ValueError(
                "A Facebook Page post supports at most 10 photos."
            )

        if any(

            not isinstance(attachment, ImageAttachment)
            for attachment in attachments
        ):
            raise ValueError(
                "All Facebook attachments must be valid images."
            )

        if not isinstance(message, str):
            raise ValueError(
                "Facebook post message must be a string."
            )

        # Validate every attachment before making any HTTP request.
        for attachment in attachments:
            FacebookImageValidator.validate(attachment)



        photo_ids: list[str] = []

        try:
            for attachment in attachments:
                photo_id = self.publish_photo(
                    page_id=page_id,
                    access_token=access_token,
                    attachment=attachment,
                    published=False,
                )
                photo_ids.append(photo_id)
        # noinspection PyBroadException
        except Exception:
            # Best-effort cleanup of confirmed unpublished uploads.
            # Never replace the original publishing exception.
            for photo_id in reversed(photo_ids):
                try:
                    self.delete_unpublished_photo(
                        photo_id=photo_id,
                        access_token=access_token,
                    )
                except (
                        FacebookApiError,
                        ValueError,
                        OSError,
                        RuntimeError,
                    ):
                    # Cleanup is best-effort; preserve the original error.
                    pass
            raise

        # Keep the feed operation outside the cleanup block:
        # its outcome may be uncertain after a network failure.
        return self.publish_photo_album(
            page_id=page_id,
            access_token=access_token,
            message=message,
            photo_ids=tuple(photo_ids),
        )

    def publish_photo_album(
        self,
        page_id: str,
        access_token: str,
        message: str,
        photo_ids: tuple[str, ...],
    ) -> str:
        """Create one Page post from unpublished photo IDs."""

        if not isinstance(page_id, str) or not page_id.strip():
            raise ValueError("A Facebook Page ID is required.")

        page_id = page_id.strip()

        if not page_id.isascii() or not page_id.isdecimal():
            raise ValueError("Invalid Facebook Page ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError(
                "A Facebook Page access token is required."
            )

        if not isinstance(message, str):
            raise ValueError(
                "Facebook post message must be a string."
            )

        if (
            not isinstance(photo_ids, tuple)
            or len(photo_ids) < 2
        ):
            raise ValueError(
                "At least two Facebook photo IDs are required."
            )

        if any(
            not isinstance(photo_id, str)
            or not photo_id
            or not photo_id.isascii()
            or not photo_id.isdecimal()
            for photo_id in photo_ids
        ):
            raise ValueError("Invalid Facebook photo ID.")

        if len(set(photo_ids)) != len(photo_ids):
            raise ValueError("Duplicate Facebook photo IDs.")

        params = {"message": message}

        for index, photo_id in enumerate(photo_ids):
            params[f"attached_media[{index}]"] = json.dumps(
                {"media_fbid": photo_id},
                separators=(",", ":"),
            )

        response = self._client.post(
            path=f"{page_id}/feed",
            access_token=access_token,
            params=params,
        )

        post_id = response.get("id")

        if not isinstance(post_id, str) or not post_id.strip():
            raise ValueError(
                "Facebook did not return a valid post ID."
            )

        return post_id.strip()
