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
