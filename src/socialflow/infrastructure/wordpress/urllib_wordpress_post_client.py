import mimetypes
from pathlib import Path
import base64
import json
import ssl
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

from socialflow.infrastructure.wordpress.wordpress_post_client import (
    WordPressPostClient,
)
from socialflow.infrastructure.wordpress.wordpress_media import (
    WordPressMedia,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent redirects from forwarding credentials."""

    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        return None


class UrllibWordPressPostClient(WordPressPostClient):
    """Create WordPress posts using HTTPS and the REST API."""

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")

        self._timeout = timeout

    def list_recent_posts(
            self,
            site_url: str,
            username: str,
            application_password: str,
            limit: int = 5,
    ) -> list[dict]:
        """Retrieve the most recent WordPress posts."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Post limit must be between 1 and 100.")

        endpoint = (
                site_url.rstrip("/")
                + "/wp-json/wp/v2/posts"
                + f"?per_page={limit}&orderby=date&order=desc"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="GET",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        with opener.open(
                request,
                timeout=self._timeout,
        ) as response:
            payload = json.load(response)

        if not isinstance(payload, list):
            raise ValueError("Invalid WordPress posts response.")

        if not all(isinstance(post, dict) for post in payload):
            raise ValueError("Invalid WordPress post entry.")

        return payload


    def list_trashed_posts(
            self,
            site_url: str,
            username: str,
            application_password: str,
            limit: int = 50,
    ) -> list[dict]:
        """Retrieve trashed WordPress posts with edit context."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError(
                "A valid HTTPS WordPress URL is required."
            )

        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError(
                "Post limit must be between 1 and 100."
            )

        endpoint = (
                site_url.rstrip("/")
                + "/wp-json/wp/v2/posts"
                + f"?status=trash&context=edit&per_page={limit}"
                + "&orderby=date&order=desc"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="GET",
        )

        opener = build_opener(
            HTTPSHandler(
                context=ssl.create_default_context()
            ),
            _NoRedirectHandler(),
        )

        with opener.open(
                request,
                timeout=self._timeout,
        ) as response:
            payload = json.load(response)

        if not isinstance(payload, list):
            raise ValueError(
                "Invalid WordPress trashed posts response."
            )

        if not all(
                isinstance(post, dict)
                and post.get("status") == "trash"
                for post in payload
        ):
            raise ValueError(
                "Invalid WordPress trashed post entry."
            )

        return payload



    def list_media(
        self,
        site_url: str,
        username: str,
        application_password: str,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve recent WordPress image media items."""

        parsed = urlsplit(site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Media limit must be between 1 and 100.")

        endpoint = (
            site_url.rstrip("/")
            + "/wp-json/wp/v2/media"
            + f"?per_page={limit}&orderby=date&order=desc"
            + "&media_type=image"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="GET",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        with opener.open(
            request,
            timeout=self._timeout,
        ) as response:
            payload = json.load(response)

        if not isinstance(payload, list):
            raise ValueError("Invalid WordPress media list response.")

        if not all(isinstance(item, dict) for item in payload):
            raise ValueError("Invalid WordPress media list entry.")

        return payload

    def create_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            content: str,
            tags: tuple[int, ...] = (),
            title: str = "",
            categories: tuple[int, ...] = (),
    ) -> int:
        parsed = urlsplit(site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        endpoint = (
            site_url.rstrip("/")
            + "/wp-json/wp/v2/posts"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        if any(
                type(tag_id) is not int or tag_id <= 0
                for tag_id in tags
        ):
            raise ValueError(
                "WordPress tag IDs must be positive integers."
            )

        if any(
            type(category_id) is not int or category_id <= 0
            for category_id in categories
        ):
            raise ValueError(
                "WordPress category IDs must be positive integers."
            )

        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                "WordPress post title must be a non-empty string."
            )

        post_data = {
            "title": title.strip(),
            "content": content,
            "status": "publish",
        }

        if tags:
            post_data["tags"] = list(tags)

        if categories:
            post_data["categories"] = list(categories)

        payload = json.dumps(post_data).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                request,
                timeout=self._timeout,
            ) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def update_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
            content: str,
            tags: tuple[int, ...] | None = None,
            featured_media_id: int | None = None,
            status: str | None = None,
            excerpt: str | None = None,
            title: str | None = None,
            categories: tuple[int, ...] | None = None,
    ) -> int:
        """Update an existing WordPress post and return its HTTP status."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        if type(post_id) is not int or post_id <= 0:
            raise ValueError("A valid WordPress post ID is required.")

        if featured_media_id is not None:
            if (
                    type(featured_media_id) is not int
                    or featured_media_id < 0
            ):
                raise ValueError(
                    "WordPress featured media ID must be "
                    "a non-negative integer."
                )

        if status is not None:
            if type(status) is not str or status not in (
                    "draft",
                    "pending",
                    "private",
                    "publish",
            ):
                raise ValueError(
                    "Unsupported WordPress post status."
                )

        if excerpt is not None and type(excerpt) is not str:
            raise ValueError(
                "WordPress post excerpt must be a string."
            )

        if title is not None:
            if type(title) is not str or not title.strip():
                raise ValueError(
                    "WordPress post title must be a non-empty string."
                )

        endpoint = (
                site_url.rstrip("/")
                + f"/wp-json/wp/v2/posts/{post_id}"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        body = {"content": content}

        if tags is not None:
            if not isinstance(tags, tuple) or any(
                    type(tag_id) is not int or tag_id <= 0
                    for tag_id in tags
            ):
                raise ValueError(
                    "WordPress tag IDs must be positive integers."
                )

            body["tags"] = list(tags)

        if categories is not None:
            if not isinstance(categories, tuple) or any(
                    type(category_id) is not int or category_id <= 0
                    for category_id in categories
            ):
                raise ValueError(
                    "WordPress category IDs must be positive integers."
                )

            body["categories"] = list(categories)

        if featured_media_id is not None:
            body["featured_media"] = featured_media_id

        if status is not None:
            body["status"] = status

        if excerpt is not None:
            body["excerpt"] = excerpt

        if title is not None:
            body["title"] = title

        payload = json.dumps(body).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                    request,
                    timeout=self._timeout,
            ) as response:
                return response.status
        except HTTPError as error:
            return error.code


    def trash_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
    ) -> int:
        """Move an existing WordPress post to Trash."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError(
                "A valid HTTPS WordPress URL is required."
            )

        if type(post_id) is not int or post_id <= 0:
            raise ValueError(
                "A valid WordPress post ID is required."
            )

        endpoint = (
            site_url.rstrip("/")
            + f"/wp-json/wp/v2/posts/{post_id}"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="DELETE",
        )

        opener = build_opener(
            HTTPSHandler(
                context=ssl.create_default_context()
            ),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                    request,
                    timeout=self._timeout,
            ) as response:
                payload = json.load(response)

                if (
                    not isinstance(payload, dict)
                    or payload.get("id") != post_id
                    or payload.get("status") != "trash"
                ):
                    raise ValueError(
                        "WordPress did not confirm the post "
                        "was moved to Trash."
                    )

                return response.status

        except HTTPError as error:
            return error.code


    def restore_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
    ) -> int:
        """Restore a trashed WordPress post to draft status."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError(
                "A valid HTTPS WordPress URL is required."
            )

        if type(post_id) is not int or post_id <= 0:
            raise ValueError(
                "A valid WordPress post ID is required."
            )

        endpoint = (
            site_url.rstrip("/")
            + f"/wp-json/wp/v2/posts/{post_id}"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        payload = json.dumps({
            "status": "draft",
        }).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        opener = build_opener(
            HTTPSHandler(
                context=ssl.create_default_context()
            ),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                    request,
                    timeout=self._timeout,
            ) as response:
                result = json.load(response)

                if (
                        not isinstance(result, dict)
                        or result.get("id") != post_id
                        or result.get("status") != "draft"
                ):
                    raise ValueError(
                        "WordPress did not confirm the post "
                        "was restored as a draft."
                    )

                return response.status

        except HTTPError as error:
            return error.code

    def upload_media(
        self,
        site_url: str,
        username: str,
        application_password: str,
        image_path: Path,
    ) -> WordPressMedia:
        """Upload an image and return its WordPress media information."""

        parsed = urlsplit(site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        image_path = Path(image_path)

        filename = image_path.name

        if any(
                character in filename
                for character in ('"', "\\", "\r", "\n")
        ) or any(ord(character) < 32 or ord(character) == 127 for character in filename):
            raise ValueError("Unsafe image filename.")

        content_type, _ = mimetypes.guess_type(image_path.name)

        if content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        }:
            raise ValueError("Unsupported WordPress image format.")

        image_data = image_path.read_bytes()

        endpoint = (
            site_url.rstrip("/")
            + "/wp-json/wp/v2/media"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            data=image_data,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
                "Content-Type": content_type,
                "Content-Disposition": (
                    f'attachment; filename="{image_path.name}"'
                ),
            },
            method="POST",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        with opener.open(
            request,
            timeout=self._timeout,
        ) as response:
            payload = json.load(response)

        if not isinstance(payload, dict):
            raise ValueError("Invalid WordPress media response.")

        media_id = payload.get("id")
        source_url = payload.get("source_url")

        if type(media_id) is not int or media_id <= 0:
            raise ValueError(
                "WordPress did not return a valid media ID."
            )

        if (
                not isinstance(source_url, str)
                or not source_url.strip()
                or not source_url.startswith("https://")
        ):
            raise ValueError(
                "WordPress did not return a valid media URL."
            )

        return WordPressMedia(
            media_id=media_id,
            source_url=source_url,
        )

    def delete_media(
            self,
            site_url: str,
            username: str,
            application_password: str,
            media_id: int,
    ) -> None:
        """Permanently delete an uploaded WordPress media item."""

        parsed = urlsplit(site_url)

        if (
                parsed.scheme.lower() != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        if type(media_id) is not int or media_id <= 0:
            raise ValueError("A valid WordPress media ID is required.")

        endpoint = (
                site_url.rstrip("/")
                + f"/wp-json/wp/v2/media/{media_id}?force=true"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="DELETE",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        with opener.open(
                request,
                timeout=self._timeout,
        ):
            pass