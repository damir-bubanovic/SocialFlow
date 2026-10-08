from datetime import datetime
from uuid import UUID

from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
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
    publication_id: UUID | None = None,
) -> Publication:
    return Publication(
        id=PublicationId(
            publication_id
            or UUID("12345678-1234-5678-1234-567812345678")
        ),
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

def test_recent_posts_panel_warns_about_missing_image(
    qtbot,
    tmp_path,
) -> None:
    image_path = tmp_path / "deleted.png"
    image_path.write_bytes(b"image content")

    repository = InMemoryPublicationRepository()
    account = create_account()

    publication = Publication(
        id=PublicationId(
            UUID("11111111-1111-1111-1111-111111111111")
        ),
        account=account,
        post=Post(
            text="Post with image",
            language=Language.ENGLISH,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=datetime(2026, 10, 8, 16, 0),
    )

    repository.add(publication)
    image_path.unlink()

    panel = RecentPostsPanel(ListRecentPublications(repository))
    qtbot.addWidget(panel)
    panel.set_account(account)

    assert panel.missing_images_warning.isHidden()

    panel.recent_posts_list.setCurrentRow(0)

    assert not panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == (
        "Warning: 1 missing image for this publication."
    )


def test_recent_posts_panel_does_not_warn_for_existing_image(
    qtbot,
    tmp_path,
) -> None:
    image_path = tmp_path / "existing.png"
    image_path.write_bytes(b"image content")

    repository = InMemoryPublicationRepository()
    account = create_account()

    publication = Publication(
        id=PublicationId(
            UUID("22222222-2222-2222-2222-222222222222")
        ),
        account=account,
        post=Post(
            text="Post with existing image",
            language=Language.ENGLISH,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=datetime(2026, 10, 8, 16, 0),
    )

    repository.add(publication)

    panel = RecentPostsPanel(ListRecentPublications(repository))
    qtbot.addWidget(panel)
    panel.set_account(account)
    panel.recent_posts_list.setCurrentRow(0)

    assert panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == ""


def test_recent_posts_panel_clears_warning_when_account_removed(
    qtbot,
    tmp_path,
) -> None:
    image_path = tmp_path / "deleted.png"
    image_path.write_bytes(b"image content")

    repository = InMemoryPublicationRepository()
    account = create_account()

    publication = Publication(
        id=PublicationId(
            UUID("33333333-3333-3333-3333-333333333333")
        ),
        account=account,
        post=Post(
            text="Post with missing image",
            language=Language.ENGLISH,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=datetime(2026, 10, 8, 16, 0),
    )

    repository.add(publication)
    image_path.unlink()

    panel = RecentPostsPanel(ListRecentPublications(repository))
    qtbot.addWidget(panel)
    panel.set_account(account)
    panel.recent_posts_list.setCurrentRow(0)

    assert not panel.missing_images_warning.isHidden()

    panel.set_account(None)

    assert panel.recent_posts_list.count() == 0
    assert panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == ""


def test_recent_posts_panel_warns_about_multiple_missing_images(
    qtbot,
    tmp_path,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"

    first_path.write_bytes(b"first image")
    second_path.write_bytes(b"second image")

    repository = InMemoryPublicationRepository()
    account = create_account()

    publication = Publication(
        id=PublicationId(
            UUID("44444444-4444-4444-4444-444444444444")
        ),
        account=account,
        post=Post(
            text="Post with two images",
            language=Language.ENGLISH,
            images=(
                ImageAttachment(path=first_path),
                ImageAttachment(path=second_path),
            ),
        ),
        published_at=datetime(2026, 10, 8, 16, 0),
    )

    repository.add(publication)
    first_path.unlink()
    second_path.unlink()

    panel = RecentPostsPanel(ListRecentPublications(repository))
    qtbot.addWidget(panel)
    panel.set_account(account)
    panel.recent_posts_list.setCurrentRow(0)

    assert not panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == (
        "Warning: 2 missing images for this publication."
    )

def test_recent_posts_panel_updates_warning_when_selection_changes(
    qtbot,
    tmp_path,
) -> None:
    image_path = tmp_path / "deleted.png"
    image_path.write_bytes(b"image content")

    repository = InMemoryPublicationRepository()
    account = create_account()

    missing_image_publication = Publication(
        id=PublicationId(
            UUID("55555555-5555-5555-5555-555555555555")
        ),
        account=account,
        post=Post(
            text="Post with missing image",
            language=Language.ENGLISH,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=datetime(2026, 10, 8, 16, 0),
    )

    valid_publication = Publication(
        id=PublicationId(
            UUID("66666666-6666-6666-6666-666666666666")
        ),
        account=account,
        post=Post(
            text="Post without missing images",
            language=Language.ENGLISH,
        ),
        published_at=datetime(2026, 10, 8, 15, 0),
    )

    repository.add(missing_image_publication)
    repository.add(valid_publication)

    image_path.unlink()

    panel = RecentPostsPanel(ListRecentPublications(repository))
    qtbot.addWidget(panel)
    panel.set_account(account)

    # Select the publication with a missing image.
    panel.recent_posts_list.setCurrentRow(0)

    assert not panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == (
        "Warning: 1 missing image for this publication."
    )

    # Select the publication without missing images.
    panel.recent_posts_list.setCurrentRow(1)

    assert panel.missing_images_warning.isHidden()
    assert panel.missing_images_warning.text() == ""

    # Select the publication with the missing image again.
    panel.recent_posts_list.setCurrentRow(0)

    assert not panel.missing_images_warning.isHidden()