import json
from datetime import datetime, timedelta
from uuid import UUID
import pytest
from unittest.mock import patch

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.domain.post.image_attachment import ImageAttachment


def create_publication(
    account: Account,
    text: str,
    published_at: datetime,
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
        published_at=published_at,
    )


def test_repository_returns_empty_history_when_file_does_not_exist(
    tmp_path,
) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert repository.recent_for_account(account) == ()


def test_repository_persists_publication(tmp_path) -> None:
    file_path = tmp_path / "publications.json"

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    publication = create_publication(
        account,
        "Hello from SocialFlow",
        datetime(2026, 10, 5, 21, 30),
    )

    repository = JsonPublicationRepository(file_path)
    repository.add(publication)

    reloaded_repository = JsonPublicationRepository(file_path)

    assert reloaded_repository.recent_for_account(account) == (
        publication,
    )


def test_repository_returns_requested_account_only(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    published_at = datetime(2026, 10, 5, 21, 30)

    facebook_publication = create_publication(
        facebook,
        "Facebook post",
        published_at,
        UUID("11111111-1111-1111-1111-111111111111"),
    )
    wordpress_publication = create_publication(
        wordpress,
        "WordPress post",
        published_at,
        UUID("22222222-2222-2222-2222-222222222222"),
    )

    repository.add(facebook_publication)
    repository.add(wordpress_publication)

    assert repository.recent_for_account(facebook) == (
        facebook_publication,
    )


def test_repository_returns_newest_publications_first(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    older = create_publication(
        account,
        "Older post",
        start,
        UUID("11111111-1111-1111-1111-111111111111"),
    )
    newer = create_publication(
        account,
        "Newer post",
        start + timedelta(minutes=1),
        UUID("22222222-2222-2222-2222-222222222222"),
    )

    repository.add(older)
    repository.add(newer)

    assert repository.recent_for_account(account) == (
        newer,
        older,
    )


def test_repository_returns_five_publications_by_default(
    tmp_path,
) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
        UUID("00000000-0000-0000-0000-000000000004"),
        UUID("00000000-0000-0000-0000-000000000005"),
        UUID("00000000-0000-0000-0000-000000000006"),
    )

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
            publication_ids[index],
        )
        for index in range(6)
    ]

    for publication in publications:
        repository.add(publication)

    assert repository.recent_for_account(account) == tuple(
        reversed(publications[1:])
    )


def test_repository_respects_custom_limit(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
    )

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
            publication_ids[index],
        )
        for index in range(3)
    ]

    for publication in publications:
        repository.add(publication)

    assert repository.recent_for_account(
        account,
        limit=2,
    ) == (
        publications[2],
        publications[1],
    )


def test_repository_migrates_legacy_publication_without_id(
    tmp_path,
) -> None:
    file_path = tmp_path / "publications.json"

    legacy_data = [
        {
            "account": {
                "name": "Main Facebook",
                "destination": "facebook",
            },
            "post": {
                "text": "Legacy publication",
                "language": "EN",
            },
            "published_at": "2026-10-05T21:30:00",
        }
    ]

    file_path.write_text(
        json.dumps(
            legacy_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository = JsonPublicationRepository(file_path)

    first_load = repository.recent_for_account(account)

    assert len(first_load) == 1
    assert isinstance(first_load[0].id, PublicationId)

    migrated_data = json.loads(
        file_path.read_text(encoding="utf-8")
    )

    assert "id" in migrated_data[0]
    assert migrated_data[0]["id"] == str(first_load[0].id)

    reloaded_repository = JsonPublicationRepository(file_path)
    second_load = reloaded_repository.recent_for_account(account)

    assert len(second_load) == 1
    assert second_load[0].id == first_load[0].id
    assert second_load[0] == first_load[0]

def test_repository_preserves_images_after_original_is_deleted(
    tmp_path,
) -> None:
    source = tmp_path / "original.png"
    source.write_bytes(b"original image content")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with image",
        datetime(2026, 10, 5, 21, 30),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=source),),
        ),
        published_at=original.published_at,
    )

    file_path = tmp_path / "publications.json"

    repository = JsonPublicationRepository(file_path)
    repository.add(publication)

    source.unlink()

    reloaded = JsonPublicationRepository(file_path)
    history = reloaded.recent_for_account(account)

    assert len(history) == 1
    assert len(history[0].post.images) == 1

    stored_image = history[0].post.images[0]

    assert stored_image.path.is_file()
    assert stored_image.path.read_bytes() == (
        b"original image content"
    )
    assert stored_image.path != source

def test_repository_removes_copied_images_when_save_fails(
    tmp_path,
) -> None:
    source = tmp_path / "original.png"
    source.write_bytes(b"image content")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with image",
        datetime(2026, 10, 5, 21, 30),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=source),),
        ),
        published_at=original.published_at,
    )

    file_path = tmp_path / "publications.json"
    repository = JsonPublicationRepository(file_path)

    with patch.object(
        repository,
        "_save",
        side_effect=OSError("Simulated save failure"),
    ):
        with pytest.raises(OSError, match="Simulated save failure"):
            repository.add(publication)

    managed_directory = tmp_path / "publication_images"

    assert not list(managed_directory.glob("*"))
    assert source.is_file()

def test_repository_preserves_existing_json_when_replace_fails(
    tmp_path,
) -> None:
    file_path = tmp_path / "publications.json"

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository = JsonPublicationRepository(file_path)

    first = create_publication(
        account,
        "Original publication",
        datetime(2026, 10, 5, 21, 30),
    )

    repository.add(first)

    original_content = file_path.read_text(encoding="utf-8")

    second = create_publication(
        account,
        "New publication",
        datetime(2026, 10, 6, 10, 0),
    )

    with patch(
        "socialflow.infrastructure.publishing.json_publication_repository.os.replace",
        side_effect=OSError("Simulated replace failure"),
    ):
        with pytest.raises(
            OSError,
            match="Simulated replace failure",
        ):
            repository.add(second)

    assert file_path.read_text(encoding="utf-8") == (
        original_content
    )

    assert not list(tmp_path.glob(".publications_*.tmp"))

def test_repository_rolls_back_when_second_image_copy_fails(
    tmp_path,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"

    first_path.write_bytes(b"first image")
    second_path.write_bytes(b"second image")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with two images",
        datetime(2026, 10, 8, 15, 0),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(
                ImageAttachment(path=first_path),
                ImageAttachment(path=second_path),
            ),
        ),
        published_at=original.published_at,
    )

    file_path = tmp_path / "publications.json"
    repository = JsonPublicationRepository(file_path)

    original_store = repository._image_storage.store
    calls = 0

    def failing_store(image):
        nonlocal calls
        calls += 1

        if calls == 2:
            raise OSError("Second image copy failed")

        return original_store(image)

    with patch.object(
        repository._image_storage,
        "store",
        side_effect=failing_store,
    ):
        with pytest.raises(
            OSError,
            match="Second image copy failed",
        ):
            repository.add(publication)

    managed_directory = tmp_path / "publication_images"

    assert not list(managed_directory.glob("*"))
    assert first_path.is_file()
    assert second_path.is_file()
    assert not file_path.exists()

def test_repository_loads_publication_when_stored_image_is_missing(
    tmp_path,
) -> None:
    source = tmp_path / "original.png"
    source.write_bytes(b"image content")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with missing image",
        datetime(2026, 10, 8, 15, 0),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=source),),
        ),
        published_at=original.published_at,
    )

    file_path = tmp_path / "publications.json"
    repository = JsonPublicationRepository(file_path)

    repository.add(publication)

    history = repository.recent_for_account(account)

    assert len(history) == 1
    assert len(history[0].post.images) == 1

    managed_image = history[0].post.images[0].path
    managed_image.unlink()

    reloaded_repository = JsonPublicationRepository(file_path)
    recovered_history = reloaded_repository.recent_for_account(
        account
    )

    assert len(recovered_history) == 1

    recovered = recovered_history[0]

    assert recovered.id == publication.id
    assert recovered.post.text == publication.post.text
    assert recovered.post.language == publication.post.language
    assert recovered.post.images == ()
    assert recovered.account == publication.account
    assert recovered.published_at == publication.published_at