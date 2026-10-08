from datetime import datetime
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.ui.posts.recent_posts_list import RecentPostsList


def create_publication(
    account_name: str,
    text: str,
    publication_id: UUID | None = None,
) -> Publication:
    """Create a publication for RecentPostsList tests."""
    return Publication(
        id=PublicationId(
            publication_id
            or UUID("12345678-1234-5678-1234-567812345678")
        ),
        account=Account(
            name=account_name,
            destination=PublishingDestination.FACEBOOK,
        ),
        post=Post(
            text=text,
            language=Language.ENGLISH,
        ),
        published_at=datetime(2026, 10, 5, 21, 0),
    )


def test_recent_posts_list_starts_empty(qtbot) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    assert recent_posts.count() == 0


def test_recent_posts_list_displays_publications(qtbot) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    publications = (
        create_publication(
            "Main Facebook",
            "First post",
            UUID("11111111-1111-1111-1111-111111111111"),
        ),
        create_publication(
            "Second Facebook",
            "Second post",
            UUID("22222222-2222-2222-2222-222222222222"),
        ),
    )

    recent_posts.set_publications(publications)

    assert recent_posts.count() == 2
    assert (
        recent_posts.item(0).text()
        == (
            "05 Oct 2026 21:00 · Facebook\n"
            "Main Facebook — First post"
        )
    )
    assert (
        recent_posts.item(1).text()
        == (
            "05 Oct 2026 21:00 · Facebook\n"
            "Second Facebook — Second post"
        )
    )


def test_recent_posts_list_replaces_existing_publications(
    qtbot,
) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    recent_posts.set_publications(
        (
            create_publication(
                "Main Facebook",
                "Old post",
                UUID("11111111-1111-1111-1111-111111111111"),
            ),
        )
    )

    recent_posts.set_publications(
        (
            create_publication(
                "Main Facebook",
                "New post",
                UUID("22222222-2222-2222-2222-222222222222"),
            ),
        )
    )

    assert recent_posts.count() == 1
    assert (
        recent_posts.item(0).text()
        == (
            "05 Oct 2026 21:00 · Facebook\n"
            "Main Facebook — New post"
        )
    )


def test_recent_posts_list_has_no_selected_publication_initially(
    qtbot,
) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    recent_posts.set_publications(
        (
            create_publication(
                "Main Facebook",
                "First post",
            ),
        )
    )

    assert recent_posts.selected_publication() is None


def test_recent_posts_list_returns_selected_publication(
    qtbot,
) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    first = create_publication(
        "Main Facebook",
        "First post",
        UUID("11111111-1111-1111-1111-111111111111"),
    )
    second = create_publication(
        "Second Facebook",
        "Second post",
        UUID("22222222-2222-2222-2222-222222222222"),
    )

    recent_posts.set_publications(
        (
            first,
            second,
        )
    )

    recent_posts.setCurrentRow(1)

    assert recent_posts.selected_publication() == second


def test_recent_posts_list_clears_selected_publication_when_replaced(
    qtbot,
) -> None:
    recent_posts = RecentPostsList()
    qtbot.addWidget(recent_posts)

    publication = create_publication(
        "Main Facebook",
        "First post",
    )

    recent_posts.set_publications(
        (
            publication,
        )
    )
    recent_posts.setCurrentRow(0)

    assert recent_posts.selected_publication() == publication

    recent_posts.set_publications(())

    assert recent_posts.selected_publication() is None