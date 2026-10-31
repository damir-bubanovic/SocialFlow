
import pytest

from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)
from socialflow.infrastructure.wordpress.wordpress_category_parser import (
    WordPressCategoryParser,
)


def test_parser_reads_categories_and_subcategories():
    payload = [
        {"id": 10, "name": "Technology", "parent": 0},
        {"id": 20, "name": "Python", "parent": 10},
        {"id": 30, "name": "Tutorials", "parent": 0},
    ]

    assert WordPressCategoryParser.parse_list(payload) == (
        WordPressCategory(id=10, name="Technology"),
        WordPressCategory(id=20, name="Python", parent_id=10),
        WordPressCategory(id=30, name="Tutorials"),
    )


def test_parser_accepts_empty_list():
    assert WordPressCategoryParser.parse_list([]) == ()


def test_parser_normalizes_names():
    result = WordPressCategoryParser.parse_list(
        [{"id": 10, "name": "  Čakovec  ", "parent": 0}]
    )

    assert result[0].name == "Čakovec"


@pytest.mark.parametrize(
    "invalid_payload",
    [
        None,
        {},
        "invalid",
        [None],
        [{"name": "Technology", "parent": 0}],
        [{"id": True, "name": "Technology", "parent": 0}],
        [{"id": 0, "name": "Technology", "parent": 0}],
        [{"id": 10, "name": "", "parent": 0}],
        [{"id": 10, "name": 123, "parent": 0}],
        [{"id": 10, "name": "Technology"}],
        [{"id": 10, "name": "Technology", "parent": -1}],
        [{"id": 10, "name": "Technology", "parent": True}],
        [{"id": 10, "name": "Technology", "parent": 10}],
    ],
)
def test_parser_rejects_invalid_payload(invalid_payload):
    with pytest.raises(ValueError):
        WordPressCategoryParser.parse_list(invalid_payload)
