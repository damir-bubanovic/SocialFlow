from datetime import datetime
import pytest

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)
from socialflow.infrastructure.wordpress.wordpress_post_parser import (
    WordPressPostParser,
)


def test_parses_wordpress_post():
    parser = WordPressPostParser()

    post = parser.parse(
        {
            "id": 42,
            "date": "2026-10-14T10:30:00",
            "content": {
                "rendered": "<p>Hello WordPress</p>",
            },
            "status": "publish",
        }
    )

    assert post == WordPressPost(
        id=42,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
    )


def test_rejects_missing_wordpress_post_id():
    parser = WordPressPostParser()

    with pytest.raises(KeyError):
        parser.parse(
            {
                "date": "2026-10-14T10:30:00",
                "content": {
                    "rendered": "<p>Hello WordPress</p>",
                },
                "status": "publish",
            }
        )


def test_wordpress_post_model_stores_tag_ids():
    post = WordPressPost(
        id=42,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
        tag_ids=(12, 34),
    )

    assert post.tag_ids == (12, 34)


def test_parses_wordpress_post_with_tags():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-14T10:30:00",
            "content": {
                "rendered": "<p>Hello WordPress</p>",
            },
            "status": "publish",
            "tags": [12, 34],
        }
    )

    assert post.tag_ids == (12, 34)


@pytest.mark.parametrize(
    "tags",
    [
        [0],
        [-1],
        [True],
        ["12"],
        [12.5],
        [None],
        "12",
        None,
    ],
)
def test_rejects_invalid_wordpress_post_tags(tags):
    with pytest.raises(
        ValueError,
        match="WordPress post tags must be positive integer IDs",
    ):
        WordPressPostParser.parse(
            {
                "id": 42,
                "date": "2026-10-14T10:30:00",
                "content": {
                    "rendered": "<p>Hello WordPress</p>",
                },
                "status": "publish",
                "tags": tags,
            }
        )

def test_parses_wordpress_post_with_featured_media():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-14T10:30:00",
            "content": {
                "rendered": "<p>Hello WordPress</p>",
            },
            "status": "publish",
            "featured_media": 123,
        }
    )

    assert post.featured_media_id == 123


@pytest.mark.parametrize(
    "featured_media",
    [
        None,
        True,
        -1,
        "123",
        12.5,
    ],
)
def test_rejects_invalid_featured_media(featured_media):
    with pytest.raises(
        ValueError,
        match="WordPress featured media ID",
    ):
        WordPressPostParser.parse(
            {
                "id": 42,
                "date": "2026-10-14T10:30:00",
                "content": {
                    "rendered": "<p>Hello WordPress</p>",
                },
                "status": "publish",
                "featured_media": featured_media,
            }
        )



@pytest.mark.parametrize(
    ("raw_excerpt", "expected"),
    [
        ("Short summary", "Short summary"),
        ("Sažetak članka čćžšđ", "Sažetak članka čćžšđ"),
        ("", ""),
    ],
)
def test_parser_preserves_wordpress_excerpt(
    raw_excerpt,
    expected,
):
    data = {
        "id": 42,
        "content": {"rendered": "<p>Existing content</p>"},
        "excerpt": {"rendered": raw_excerpt},
        "date": "2026-10-26T12:00:00",
        "status": "publish",
        "tags": [],
        "featured_media": 0,
    }

    post = WordPressPostParser.parse(data)

    assert post.excerpt == expected


def test_parser_defaults_missing_excerpt_to_empty_string():
    data = {
        "id": 42,
        "content": {"rendered": "<p>Existing content</p>"},
        "date": "2026-10-26T12:00:00",
        "status": "publish",
        "tags": [],
        "featured_media": 0,
    }

    post = WordPressPostParser.parse(data)

    assert post.excerpt == ""



def test_parser_prefers_raw_excerpt_over_rendered():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "content": {"rendered": "<p>Content</p>"},
            "excerpt": {
                "raw": "Sažetak čćžšđ",
                "rendered": "<p>Sažetak čćžšđ</p>",
            },
            "date": "2026-10-26T12:00:00",
            "status": "publish",
        }
    )

    assert post.excerpt == "Sažetak čćžšđ"


@pytest.mark.parametrize(
    "invalid_excerpt",
    [
        None,
        "Plain text",
        [],
        {"raw": 123},
        {"rendered": False},
    ],
)
def test_parser_rejects_invalid_excerpt_data(
    invalid_excerpt,
):
    with pytest.raises(ValueError, match="excerpt"):
        WordPressPostParser.parse(
            {
                "id": 42,
                "content": {"rendered": "<p>Content</p>"},
                "excerpt": invalid_excerpt,
                "date": "2026-10-26T12:00:00",
                "status": "publish",
            }
        )



@pytest.mark.parametrize(
    ("title_data", "expected"),
    [
        (
            {"rendered": "WordPress title"},
            "WordPress title",
        ),
        (
            {"rendered": "Naslov članka čćžšđ"},
            "Naslov članka čćžšđ",
        ),
        (
            {
                "raw": "Editable title",
                "rendered": "Rendered title",
            },
            "Editable title",
        ),
        (
            {"rendered": ""},
            "",
        ),
    ],
)
def test_parser_preserves_wordpress_title(
    title_data,
    expected,
):
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-26T12:00:00",
            "content": {"rendered": "<p>Content</p>"},
            "status": "publish",
            "title": title_data,
        }
    )

    assert post.title == expected


def test_parser_defaults_missing_title_to_empty_string():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-26T12:00:00",
            "content": {"rendered": "<p>Content</p>"},
            "status": "publish",
        }
    )

    assert post.title == ""


@pytest.mark.parametrize(
    "invalid_title",
    [
        None,
        "Plain string",
        123,
        [],
        {"raw": 123},
        {"rendered": None},
        {"raw": False},
    ],
)
def test_parser_rejects_invalid_wordpress_title(
    invalid_title,
):
    with pytest.raises(ValueError, match="WordPress post title"):
        WordPressPostParser.parse(
            {
                "id": 42,
                "date": "2026-10-26T12:00:00",
                "content": {"rendered": "<p>Content</p>"},
                "status": "publish",
                "title": invalid_title,
            }
        )



def test_parser_preserves_wordpress_categories():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-31T10:30:00",
            "content": {"rendered": "<p>Content</p>"},
            "status": "publish",
            "categories": [10, 20],
        }
    )

    assert post.category_ids == (10, 20)


def test_parser_defaults_missing_categories_to_empty_tuple():
    post = WordPressPostParser.parse(
        {
            "id": 42,
            "date": "2026-10-31T10:30:00",
            "content": {"rendered": "<p>Content</p>"},
            "status": "publish",
        }
    )

    assert post.category_ids == ()


@pytest.mark.parametrize(
    "categories",
    [
        None,
        "10",
        [0],
        [-1],
        [True],
        ["10"],
        [10.5],
        [None],
    ],
)
def test_parser_rejects_invalid_wordpress_categories(categories):
    with pytest.raises(
        ValueError,
        match="WordPress post categories must be positive integer IDs",
    ):
        WordPressPostParser.parse(
            {
                "id": 42,
                "date": "2026-10-31T10:30:00",
                "content": {"rendered": "<p>Content</p>"},
                "status": "publish",
                "categories": categories,
            }
        )
