from datetime import datetime

from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
)
from socialflow.ui.posts.recent_posts_panel import RecentPostsPanel


def create_account() -> Account:
    return Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )


def create_publication(
    account: Account,
    text: str,
) -> Publication:
    return Publication(
        account=account,
        post=Post(
            text=text,
            language=Language.ENGLISH,
        ),
        published_at=datetime(2026, 10, 5, 21, 0),
    )


def test_recent_posts_panel_starts_empty(qtbot) -> None:
    repository = InMemoryPublicationRepository()

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    assert panel.recent_posts_list.count() == 0


def test_recent_posts_panel_displays_account_history(qtbot) -> None:
    repository = InMemoryPublicationRepository()
    account = create_account()

    repository.add(
        create_publication(
            account,
            "Hello from SocialFlow",
        )
    )

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    panel.set_account(account)

    assert panel.recent_posts_list.count() == 1
    assert (
            panel.recent_posts_list.item(0).text()
            == (
                "05 Oct 2026 21:00 · Facebook\n"
                "Main Facebook — Hello from SocialFlow"
            )
    )


def test_recent_posts_panel_clears_when_account_is_removed(
    qtbot,
) -> None:
    repository = InMemoryPublicationRepository()
    account = create_account()

    repository.add(
        create_publication(
            account,
            "Hello from SocialFlow",
        )
    )

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    panel.set_account(account)

    assert panel.recent_posts_list.count() == 1

    panel.set_account(None)

    assert panel.recent_posts_list.count() == 0


def test_recent_posts_panel_refreshes_history(qtbot) -> None:
    repository = InMemoryPublicationRepository()
    account = create_account()

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    panel.set_account(account)

    assert panel.recent_posts_list.count() == 0

    repository.add(
        create_publication(
            account,
            "New publication",
        )
    )

    panel.refresh()

    assert panel.recent_posts_list.count() == 1
    assert (
            panel.recent_posts_list.item(0).text()
            == (
                "05 Oct 2026 21:00 · Facebook\n"
                "Main Facebook — New publication"
            )
    )

def test_recent_posts_panel_emits_selected_publication(
    qtbot,
) -> None:
    repository = InMemoryPublicationRepository()
    account = create_account()

    publication = create_publication(
        account,
        "Hello from SocialFlow",
    )
    repository.add(publication)

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    panel.set_account(account)

    with qtbot.waitSignal(
        panel.publication_selected,
        timeout=1000,
    ) as blocker:
        panel.recent_posts_list.setCurrentRow(0)

    assert blocker.args == [publication]


def test_recent_posts_panel_does_not_emit_when_history_is_cleared(
    qtbot,
) -> None:
    repository = InMemoryPublicationRepository()
    account = create_account()

    repository.add(
        create_publication(
            account,
            "Hello from SocialFlow",
        )
    )

    panel = RecentPostsPanel(
        ListRecentPublications(repository)
    )
    qtbot.addWidget(panel)

    panel.set_account(account)

    emissions = []

    panel.publication_selected.connect(
        emissions.append
    )

    panel.set_account(None)

    assert emissions == []