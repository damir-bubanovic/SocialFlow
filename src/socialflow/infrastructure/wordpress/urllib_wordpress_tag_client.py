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

from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.infrastructure.wordpress.wordpress_tag_parser import (
    WordPressTagParser,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent redirects from forwarding authentication credentials."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UrllibWordPressTagClient(WordPressTagClient):
    """Retrieve WordPress tags using the authenticated REST API."""

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")

        self._timeout = timeout

    @staticmethod
    def _validate_site_url(site_url: str) -> None:
        """Validate the WordPress site URL before sending credentials."""
        parsed = urlsplit(site_url)

        try:
            if parsed.port is not None and parsed.port <= 0:
                raise ValueError("Invalid port.")
        except ValueError as error:
            raise ValueError(
                "A valid HTTPS WordPress URL is required."
            ) from error

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or "/wp-json/" in parsed.path.lower()
            or ".." in parsed.path.split("/")
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

    def list_tags(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> tuple[WordPressTag, ...]:
        """Retrieve all pages of WordPress tags."""
        self._validate_site_url(site_url)

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        tags = []
        total_pages = None
        page = 1

        while total_pages is None or page <= total_pages:
            endpoint = (
                site_url.rstrip("/")
                + "/wp-json/wp/v2/tags"
                + f"?per_page=100&page={page}"
            )

            request = Request(
                endpoint,
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Accept": "application/json",
                },
                method="GET",
            )

            with opener.open(
                request,
                timeout=self._timeout,
            ) as response:
                payload = json.load(response)

                raw_total_pages = response.headers.get(
                    "X-WP-TotalPages"
                )

                try:
                    response_total_pages = int(raw_total_pages)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        "Invalid WordPress pagination header."
                    ) from error

                if not 1 <= response_total_pages <= 1000:
                    raise ValueError(
                        "Invalid WordPress pagination page count."
                    )

                if total_pages is None:
                    total_pages = response_total_pages
                elif response_total_pages != total_pages:
                    raise ValueError(
                        "Inconsistent WordPress pagination headers."
                    )

            page_tags = WordPressTagParser.parse_list(payload)

            if not page_tags and page < total_pages:
                raise ValueError(
                    "WordPress returned an incomplete tag collection."
                )

            tags.extend(page_tags)
            page += 1

        return tuple(tags)


    def create_tag(
        self,
        site_url: str,
        username: str,
        application_password: str,
        name: str,
    ) -> WordPressTag:
        """Create a WordPress tag using the authenticated REST API."""
        self._validate_site_url(site_url)

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("WordPress tag name cannot be empty.")

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        endpoint = site_url.rstrip("/") + "/wp-json/wp/v2/tags"

        payload = json.dumps(
            {"name": normalized_name}
        ).encode("utf-8")

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
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                    request,
                    timeout=self._timeout,
            ) as response:
                response_payload = json.load(response)

        except HTTPError as error:
            if error.code != 400:
                raise

            try:
                error_payload = json.loads(error.read())
            except (ValueError, UnicodeDecodeError):
                raise error

            if not isinstance(error_payload, dict):
                raise error

            if error_payload.get("code") != "term_exists":
                raise error

            data = error_payload.get("data")

            if not isinstance(data, dict):
                raise error

            if data.get("status") != 400:
                raise error

            term_id = data.get("term_id")

            if (
                    not isinstance(term_id, int)
                    or isinstance(term_id, bool)
                    or term_id <= 0
            ):
                raise error

            return WordPressTag(
                id=term_id,
                name=normalized_name,
            )

        return WordPressTagParser.parse_list([response_payload])[0]
