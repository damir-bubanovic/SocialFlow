import pytest

from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
    WordPressTagResolver,
)


def test_resolves_selected_tags_in_order() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("SocialFlow"), Tag("Python")),
        (WordPressTag(12, "Python"), WordPressTag(34, "SocialFlow")),
    )
    assert result == (34, 12)


def test_matches_names_case_insensitively() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("PYTHON"),),
        (WordPressTag(12, "Python"),),
    )
    assert result == (12,)


def test_deduplicates_selected_tags() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("Python"), Tag("python")),
        (WordPressTag(12, "Python"),),
    )
    assert result == (12,)


def test_empty_selection_returns_empty_tuple() -> None:
    assert WordPressTagResolver().resolve((), ()) == ()


def test_missing_tag_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="WordPress tag not found: Missing",
    ):
        WordPressTagResolver().resolve(
            (Tag("Missing"),),
            (),
        )


def test_ambiguous_remote_name_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="Ambiguous WordPress tag: Python",
    ):
        WordPressTagResolver().resolve(
            (Tag("Python"),),
            (
                WordPressTag(12, "Python"),
                WordPressTag(34, "python"),
            ),
        )


def test_duplicate_remote_id_is_not_ambiguous() -> None:
    assert WordPressTagResolver().resolve(
        (Tag("Python"),),
        (
            WordPressTag(12, "Python"),
            WordPressTag(12, "python"),
        ),
    ) == (12,)

def test_find_missing_wordpress_tags() -> None:
    missing = WordPressTagResolver.find_missing(
        selected_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
            Tag("Linux"),
        ),
        remote_tags=(
            WordPressTag(id=12, name="Python"),
        ),
    )

    assert missing == (
        Tag("SocialFlow"),
        Tag("Linux"),
    )


def test_find_missing_matches_case_insensitively() -> None:
    missing = WordPressTagResolver.find_missing(
        selected_tags=(Tag("PYTHON"),),
        remote_tags=(WordPressTag(id=12, name="Python"),),
    )

    assert missing == ()


def test_find_missing_removes_duplicates() -> None:
    missing = WordPressTagResolver.find_missing(
        selected_tags=(
            Tag("SocialFlow"),
            Tag("socialflow"),
        ),
        remote_tags=(),
    )

    assert missing == (Tag("SocialFlow"),)


def test_find_missing_returns_empty_when_all_exist() -> None:
    missing = WordPressTagResolver.find_missing(
        selected_tags=(Tag("Python"),),
        remote_tags=(WordPressTag(id=12, name="Python"),),
    )

    assert missing == ()


def test_find_missing_handles_empty_selection() -> None:
    missing = WordPressTagResolver.find_missing(
        selected_tags=(),
        remote_tags=(),
    )

    assert missing == ()

def test_prepare_creation_plan_with_missing_tags():
    plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
        remote_tags=(
            WordPressTag(id=12, name="Python"),
        ),
    )

    assert plan.requires_confirmation is True
    assert plan.tag_names == ("SocialFlow",)


def test_prepare_creation_plan_when_all_tags_exist():
    plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=(Tag("Python"),),
        remote_tags=(
            WordPressTag(id=12, name="Python"),
        ),
    )

    assert plan.requires_confirmation is False
    assert plan.missing_tags == ()


def test_prepare_creation_plan_without_selected_tags():
    plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=(),
        remote_tags=(),
    )

    assert plan.requires_confirmation is False
    assert plan.tag_names == ()

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("čakovec", "Čakovec"),
        ("HRVATSKA", "hrvatska"),
        ("ŽIVOT", "život"),
        ("Šibenik", "šIBENIK"),
        ("Đakovo", "đAKOVO"),
        ("PYTHON", "Python"),
    ],
)
def test_resolver_matches_existing_tags_case_insensitively(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (
        Tag(selected_name),
    )

    remote_tags = (
        WordPressTag(id=101, name=remote_name),
    )

    missing_tags = WordPressTagResolver.find_missing(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert missing_tags == ()

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("café", "cafe\u0301"),
        ("Čakovec", "C\u030Cakovec"),
        ("Šibenik", "S\u030Cibenik"),
        ("Život", "Z\u030Civot"),
        ("Đakovo", "ĐAKOVO"),
    ],
)
def test_resolver_matches_unicode_equivalent_tags(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (
        Tag(selected_name),
    )

    remote_tags = (
        WordPressTag(id=101, name=remote_name),
    )

    missing_tags = WordPressTagResolver.find_missing(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert missing_tags == ()

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("café", "cafe\u0301"),
        ("Čakovec", "C\u030Cakovec"),
        ("Šibenik", "S\u030Cibenik"),
        ("Život", "Z\u030Civot"),
        ("Đakovo", "ĐAKOVO"),
    ],
)
def test_resolver_returns_existing_id_for_unicode_equivalent_tag(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (
        Tag(selected_name),
    )

    remote_tags = (
        WordPressTag(id=101, name=remote_name),
    )

    resolved_ids = WordPressTagResolver.resolve(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert resolved_ids == (101,)

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("ÅNGSTRÖM", "a\u030angstro\u0308m"),
        ("CAFÉ", "cafe\u0301"),
        ("ČAKOVEC", "c\u030cakovec"),
        ("ŠIBENIK", "s\u030cibenik"),
    ],
)
def test_resolver_matches_combined_casefold_and_unicode_normalization(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (Tag(selected_name),)
    remote_tags = (WordPressTag(id=101, name=remote_name),)

    missing_tags = WordPressTagResolver.find_missing(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    resolved_ids = WordPressTagResolver.resolve(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert missing_tags == ()
    assert resolved_ids == (101,)

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("Straße", "STRASSE"),
        ("STRASSE", "straße"),
        ("Maße", "MASSE"),
        ("WEISS", "weiß"),
    ],
)
def test_resolver_handles_casefold_expansion(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (Tag(selected_name),)
    remote_tags = (WordPressTag(id=101, name=remote_name),)

    missing_tags = WordPressTagResolver.find_missing(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    resolved_ids = WordPressTagResolver.resolve(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert missing_tags == ()
    assert resolved_ids == (101,)

def test_resolver_deduplicates_equivalent_missing_tags() -> None:
    selected_tags = (
        Tag("Čakovec"),
        Tag("čakovec"),
        Tag("C\u030Cakovec"),
        Tag("Šibenik"),
        Tag("šIBENIK"),
    )

    missing_tags = WordPressTagResolver.find_missing(
        selected_tags=selected_tags,
        remote_tags=(),
    )

    assert missing_tags == (
        Tag("Čakovec"),
        Tag("Šibenik"),
    )


def test_resolver_deduplicates_existing_tag_ids() -> None:
    selected_tags = (
        Tag("Čakovec"),
        Tag("čakovec"),
        Tag("C\u030Cakovec"),
        Tag("Šibenik"),
        Tag("šIBENIK"),
    )

    remote_tags = (
        WordPressTag(id=101, name="Čakovec"),
        WordPressTag(id=202, name="Šibenik"),
    )

    resolved_ids = WordPressTagResolver.resolve(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert resolved_ids == (101, 202)

def test_resolver_accepts_duplicate_remote_entries_with_same_id() -> None:
    selected_tags = (
        Tag("Čakovec"),
    )

    remote_tags = (
        WordPressTag(id=101, name="Čakovec"),
        WordPressTag(id=101, name="čakovec"),
        WordPressTag(id=101, name="C\u030Cakovec"),
    )

    resolved_ids = WordPressTagResolver.resolve(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert resolved_ids == (101,)


def test_resolver_rejects_ambiguous_remote_tag_ids() -> None:
    selected_tags = (
        Tag("Čakovec"),
    )

    remote_tags = (
        WordPressTag(id=101, name="Čakovec"),
        WordPressTag(id=202, name="čakovec"),
    )

    with pytest.raises(
        ValueError,
        match="Ambiguous WordPress tag: Čakovec",
    ):
        WordPressTagResolver.resolve(
            selected_tags=selected_tags,
            remote_tags=remote_tags,
        )

@pytest.mark.parametrize(
    ("selected_name", "remote_name"),
    [
        ("Čakovec", "C\u030Cakovec"),
        ("Šibenik", "S\u030Cibenik"),
        ("Život", "Z\u030Civot"),
        ("café", "cafe\u0301"),
    ],
)
def test_resolver_rejects_unicode_equivalent_ambiguous_remote_ids(
    selected_name: str,
    remote_name: str,
) -> None:
    selected_tags = (
        Tag(selected_name),
    )

    remote_tags = (
        WordPressTag(id=101, name=selected_name),
        WordPressTag(id=202, name=remote_name),
    )

    with pytest.raises(
        ValueError,
        match=f"Ambiguous WordPress tag: {selected_name}",
    ):
        WordPressTagResolver.resolve(
            selected_tags=selected_tags,
            remote_tags=remote_tags,
        )

def test_prepare_creation_plan_rejects_ambiguous_existing_tags() -> None:
    selected_tags = (
        Tag("Čakovec"),
        Tag("SocialFlow"),
    )

    remote_tags = (
        WordPressTag(id=101, name="Čakovec"),
        WordPressTag(id=202, name="C\u030Cakovec"),
    )

    with pytest.raises(
        ValueError,
        match="Ambiguous WordPress tag: Čakovec",
    ):
        WordPressTagResolver.prepare_creation_plan(
            selected_tags=selected_tags,
            remote_tags=remote_tags,
        )


def test_prepare_creation_plan_accepts_existing_and_missing_tags() -> None:
    selected_tags = (
        Tag("Čakovec"),
        Tag("čakovec"),
        Tag("SocialFlow"),
        Tag("socialflow"),
        Tag("Šibenik"),
    )

    remote_tags = (
        WordPressTag(id=101, name="C\u030Cakovec"),
    )

    plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert plan.missing_tags == (
        Tag("SocialFlow"),
        Tag("Šibenik"),
    )

def test_prepare_creation_plan_accepts_generator_inputs() -> None:
    selected_tags = (
        Tag(name)
        for name in (
            "Čakovec",
            "SocialFlow",
            "Šibenik",
        )
    )

    remote_tags = (
        WordPressTag(id=tag_id, name=name)
        for tag_id, name in (
            (101, "C\u030Cakovec"),
            (202, "Šibenik"),
        )
    )

    plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    assert plan.missing_tags == (
        Tag("SocialFlow"),
    )