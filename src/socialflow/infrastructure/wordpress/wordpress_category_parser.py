
from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)


class WordPressCategoryParser:
    """Convert WordPress category responses into validated models."""

    @staticmethod
    def parse_list(data: object) -> tuple[WordPressCategory, ...]:
        if not isinstance(data, list):
            raise ValueError("Invalid WordPress categories response.")

        categories = []

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Invalid WordPress category entry.")

            category_id = item.get("id")
            name = item.get("name")
            parent_id = item.get("parent")

            if type(category_id) is not int or category_id <= 0:
                raise ValueError("Invalid WordPress category ID.")

            if not isinstance(name, str) or not name.strip():
                raise ValueError("Invalid WordPress category name.")

            if type(parent_id) is not int or parent_id < 0:
                raise ValueError("Invalid WordPress category parent ID.")

            categories.append(
                WordPressCategory(
                    id=category_id,
                    name=name,
                    parent_id=parent_id,
                )
            )

        return tuple(categories)
