import pytest

from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_parser import (
    WordPressTagParser,
)


def test_parser_converts_wordpress_tag_list() -> None:
    data = [
        {"id": 10, "name": "Python", "slug": "python"},
        {"id": 20, "name": "SocialFlow", "count": 3},
    ]

    result = WordPressTagParser.parse_list(data)

    assert result == (
        WordPressTag(id=10, name="Python"),
        WordPressTag(id=20, name="SocialFlow"),
    )


def test_parser_accepts_empty_list() -> None:
    assert WordPressTagParser.parse_list([]) == ()


@pytest.mark.parametrize(
    "invalid_data",
    [
        None,
        {},
        "invalid",
        [{"name": "Python"}],
        [{"id": 0, "name": "Python"}],
        [{"id": True, "name": "Python"}],
        [{"id": 1, "name": ""}],
        [{"id": 1, "name": 123}],
        [None],
    ],
)
def test_parser_rejects_invalid_responses(invalid_data) -> None:
    with pytest.raises(ValueError):
        WordPressTagParser.parse_list(invalid_data)