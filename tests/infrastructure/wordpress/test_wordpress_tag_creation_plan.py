from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)


def test_plan_requires_confirmation_for_missing_tags():
    plan = WordPressTagCreationPlan(
        missing_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
    )

    assert plan.requires_confirmation is True


def test_plan_does_not_require_confirmation_when_empty():
    plan = WordPressTagCreationPlan(
        missing_tags=(),
    )

    assert plan.requires_confirmation is False


def test_plan_returns_missing_tag_names():
    plan = WordPressTagCreationPlan(
        missing_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
    )

    assert plan.tag_names == (
        "Python",
        "SocialFlow",
    )


def test_plan_is_immutable():
    plan = WordPressTagCreationPlan(
        missing_tags=(Tag("Python"),),
    )

    assert plan.missing_tags == (Tag("Python"),)