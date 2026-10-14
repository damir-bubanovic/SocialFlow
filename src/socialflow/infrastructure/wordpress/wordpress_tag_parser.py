from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


class WordPressTagParser:
    """Convert WordPress REST API tag data into validated models."""

    @staticmethod
    def parse_list(data: object) -> tuple[WordPressTag, ...]:
        if not isinstance(data, list):
            raise ValueError("Invalid WordPress tags response.")

        tags = []

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Invalid WordPress tag entry.")

            tag_id = item.get("id")
            name = item.get("name")

            if type(tag_id) is not int or tag_id <= 0:
                raise ValueError("Invalid WordPress tag ID.")

            if not isinstance(name, str):
                raise ValueError("Invalid WordPress tag name.")

            tags.append(WordPressTag(id=tag_id, name=name))

        return tuple(tags)