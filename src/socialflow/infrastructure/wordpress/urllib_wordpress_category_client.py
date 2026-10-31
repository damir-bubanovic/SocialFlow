
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

from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)
from socialflow.infrastructure.wordpress.wordpress_category_client import (
    WordPressCategoryClient,
)
from socialflow.infrastructure.wordpress.wordpress_category_parser import (
    WordPressCategoryParser,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not forward credentials to redirect destinations."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UrllibWordPressCategoryClient(WordPressCategoryClient):
    """Authenticated WordPress category API client."""

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")
        self._timeout = timeout

    @staticmethod
    def _validate_site_url(site_url: str) -> None:
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
            raise ValueError(
                "A valid HTTPS WordPress URL is required."
            )

    @staticmethod
    def _authorization(username: str, password: str) -> str:
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")
        return f"Basic {encoded}"

    @staticmethod
    def _opener():
        return build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

    def list_categories(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> tuple[WordPressCategory, ...]:
        self._validate_site_url(site_url)

        authorization = self._authorization(
            username, application_password
        )
        opener = self._opener()

        categories = []
        total_pages = None
        page = 1

        while total_pages is None or page <= total_pages:
            endpoint = (
                site_url.rstrip("/")
                + "/wp-json/wp/v2/categories"
                + f"?per_page=100&page={page}"
            )

            request = Request(
                endpoint,
                headers={
                    "Authorization": authorization,
                    "Accept": "application/json",
                },
                method="GET",
            )

            with opener.open(
                request, timeout=self._timeout
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

            page_categories = WordPressCategoryParser.parse_list(
                payload
            )

            if not page_categories and page < total_pages:
                raise ValueError(
                    "WordPress returned an incomplete category collection."
                )

            categories.extend(page_categories)
            page += 1

        return tuple(categories)

    def create_category(
        self,
        site_url: str,
        username: str,
        application_password: str,
        name: str,
        parent_id: int = 0,
    ) -> WordPressCategory:
        self._validate_site_url(site_url)

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError(
                "WordPress category name cannot be empty."
            )

        if type(parent_id) is not int or parent_id < 0:
            raise ValueError(
                "WordPress parent category ID must be non-negative."
            )

        endpoint = (
            site_url.rstrip("/") + "/wp-json/wp/v2/categories"
        )

        payload = json.dumps({
            "name": normalized_name,
            "parent": parent_id,
        }).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": self._authorization(
                    username, application_password
                ),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        opener = self._opener()

        try:
            with opener.open(
                request, timeout=self._timeout
            ) as response:
                response_payload = json.load(response)

        except HTTPError as error:
            if error.code != 400:
                raise

            try:
                error_payload = json.loads(error.read())
            except (ValueError, UnicodeDecodeError):
                raise error

            if (
                not isinstance(error_payload, dict)
                or error_payload.get("code") != "term_exists"
            ):
                raise error

            data = error_payload.get("data")
            if (
                not isinstance(data, dict)
                or data.get("status") != 400
            ):
                raise error

            term_id = data.get("term_id")
            if type(term_id) is not int or term_id <= 0:
                raise error

            # Do not assume an existing category has the
            # requested parent. Retrieve and verify it.
            existing = self.list_categories(
                site_url,
                username,
                application_password,
            )
            for category in existing:
                if category.id == term_id:
                    if category.parent_id != parent_id:
                        raise ValueError(
                            "Existing category has a different parent."
                        )
                    return category

            raise ValueError(
                "Existing WordPress category could not be verified."
            ) from error

        category = WordPressCategoryParser.parse_list(
            [response_payload]
        )[0]

        if category.parent_id != parent_id:
            raise ValueError(
                "Created WordPress category has an unexpected parent."
            )

        return category
