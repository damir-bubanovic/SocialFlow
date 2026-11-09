import pytest
import json

from PySide6.QtWidgets import QStackedWidget, QWidget

from socialflow.modules.accounts.views.accounts_page import AccountsPage
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
)
from socialflow.modules.accounts.controllers.facebook_page_discovery_controller import (
    FacebookPageDiscoveryController,
)
from socialflow.modules.facebook.services.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.services.facebook_connection_verifier import (
    FacebookConnectionVerifier,
)
from socialflow.modules.accounts.controllers.facebook_verification_controller import (
    FacebookVerificationController,
)
from socialflow.ui.main_content import MainContent
from socialflow.ui.navigation import Navigation
from socialflow.modules.posts.views.posts_page import PostsPage
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.modules.posts.repositories.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.modules.wordpress.auth.wordpress_connection_verifier import (
    WordPressConnectionVerifier,
)
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.modules.wordpress.adapters.wordpress_publisher import (
    WordPressPublisher,
)
from socialflow.modules.wordpress.api.urllib_wordpress_tag_client import (
    UrllibWordPressTagClient,
)
from socialflow.modules.posts.services.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.modules.wordpress.adapters.wordpress_post_trasher import (
    WordPressPostTrasher,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)
from socialflow.modules.accounts.models.account_id import AccountId
from uuid import uuid4
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.repositories.errors import (
    AccountStorageError,
)


@pytest.fixture(autouse=True)
def isolate_socialflow_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "XDG_DATA_HOME",
        str(tmp_path),
    )


def test_main_content_is_widget(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content, QWidget)


def test_main_content_contains_navigation(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.navigation, Navigation)


def test_main_content_contains_page_stack(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.pages, QStackedWidget)


def test_main_content_contains_posts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.posts_page, PostsPage)


def test_main_content_contains_accounts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.accounts_page, AccountsPage)

def test_main_content_wires_facebook_connection_verifier(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    verifier = content.facebook_connection_verifier

    assert isinstance(
        verifier,
        FacebookConnectionVerifier,
    )

    controller = (
        content.accounts_page._facebook_verification_controller
    )

    assert isinstance(
        controller,
        FacebookVerificationController,
    )
    assert controller._verifier is verifier
    assert isinstance(
        verifier._graph_client,
        FacebookGraphClient,
    )
    assert not controller.is_running

def test_main_content_wires_facebook_account_services(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    accounts_page = content.accounts_page

    assert isinstance(
        accounts_page._save_facebook_credentials,
        SaveFacebookCredentials,
    )
    assert isinstance(
        accounts_page._get_facebook_credentials,
        GetFacebookCredentials,
    )
    assert isinstance(
        accounts_page._delete_facebook_credentials,
        DeleteFacebookCredentials,
    )

    controller = accounts_page._facebook_discovery_controller

    assert isinstance(
        controller,
        FacebookPageDiscoveryController,
    )
    assert isinstance(
        controller._discovery_service,
        FacebookPageDiscoveryService,
    )
    assert isinstance(
        controller._discovery_service._client,
        FacebookGraphClient,
    )


def test_posts_page_is_selected_by_default(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert content.pages.currentWidget() is content.posts_page


def test_accounts_navigation_shows_accounts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.navigation.tab_bar.setCurrentIndex(
        Navigation.ACCOUNTS_INDEX
    )

    assert content.pages.currentWidget() is content.accounts_page


def test_posts_navigation_shows_posts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.navigation.tab_bar.setCurrentIndex(
        Navigation.ACCOUNTS_INDEX
    )
    content.navigation.tab_bar.setCurrentIndex(
        Navigation.POSTS_INDEX
    )

    assert content.pages.currentWidget() is content.posts_page

def test_adding_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert (
        len(content.posts_page.post_editor.destination_selector._checkboxes)
        == 0
    )

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.destination_input.setCurrentIndex(
        content.accounts_page.account_form.destination_input.findData(
            PublishingDestination.FACEBOOK
        )
    )
    content.accounts_page.account_form.add_button.click()

    checkboxes = (
        content.posts_page.post_editor.destination_selector._checkboxes
    )

    assert len(checkboxes) == 1
    assert checkboxes[0].text() == "Main Facebook (Facebook)"

def test_updating_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.destination_input.setCurrentIndex(
        content.accounts_page.account_form.destination_input.findData(
            PublishingDestination.FACEBOOK
        )
    )
    content.accounts_page.account_form.add_button.click()

    content.accounts_page.account_list.setCurrentRow(0)
    content.accounts_page.account_form.name_input.setText(
        "Updated Facebook"
    )
    content.accounts_page.update_button.click()

    checkboxes = (
        content.posts_page.post_editor.destination_selector._checkboxes
    )

    assert len(checkboxes) == 1
    assert checkboxes[0].text() == "Updated Facebook (Facebook)"


def test_removing_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.add_button.click()

    content.accounts_page.account_list.setCurrentRow(0)
    content.accounts_page.remove_button.click()

    assert (
        len(content.posts_page.post_editor.destination_selector._checkboxes)
        == 0
    )

def test_main_content_does_not_persist_unconfigured_publication(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "XDG_DATA_HOME",
        str(tmp_path),
    )

    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    content = MainContent()
    qtbot.addWidget(content)

    assert (
        len(
            content.posts_page
            .post_editor
            .destination_selector
            ._checkboxes
        )
        == 1
    )

    content.posts_page.post_editor.text_editor.setPlainText(
        "Persistent history test"
    )

    content.posts_page.post_editor.destination_selector._checkboxes[
        0
    ].setChecked(True)

    with qtbot.waitSignal(
            content.posts_page.publishing_finished,
            timeout=5000,
    ):
        content.posts_page.post_editor.publish_button.click()

    publication_repository = JsonPublicationRepository(
        paths.publications_file
    )

    publications = publication_repository.recent_for_account(
        account
    )

    assert publications == ()

def test_main_content_displays_unconfigured_publishing_error(
    qtbot,
) -> None:
    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    content = MainContent()
    qtbot.addWidget(content)

    editor = content.posts_page.post_editor

    editor.text_editor.setPlainText(
        "Testing unconfigured publishing"
    )

    editor.destination_selector._checkboxes[0].setChecked(True)

    with qtbot.waitSignal(
            content.posts_page.publishing_finished,
            timeout=5000,
    ):
        editor.publish_button.click()

    assert content.posts_page.publish_status.text() == (
        "Main Facebook — Failed: "
        "Publishing configuration needs attention."
    )

    assert (
        content.posts_page.publish_status.property("status")
        == "error"
    )

    publication_repository = JsonPublicationRepository(
        paths.publications_file
    )

    assert publication_repository.recent_for_account(account) == ()

def test_main_content_migrates_legacy_publications_on_startup(
    qtbot,
) -> None:
    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    legacy_publication = {
        "id": "12345678-1234-5678-1234-567812345678",
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

    paths.publications_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.publications_file.write_text(
        json.dumps([legacy_publication]),
        encoding="utf-8",
    )

    # Initializing MainContent must trigger migration.
    content = MainContent()
    qtbot.addWidget(content)

    stored_publications = json.loads(
        paths.publications_file.read_text(
            encoding="utf-8",
        )
    )

    assert len(stored_publications) == 1

    assert (
        stored_publications[0]["account"]["id"]
        == str(account.id)
    )

    assert (
        stored_publications[0]["post"]["text"]
        == "Legacy publication"
    )

def test_main_content_initializes_wordpress_verifier(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(
        content.wordpress_connection_verifier,
        WordPressConnectionVerifier,
    )

def test_main_content_configures_wordpress_publisher_with_tag_client(
    qtbot,
) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    account = Account(
        name="WordPress Tag Test",
        destination=PublishingDestination.WORDPRESS,
    )

    router = content.posts_page._publishing_controller._publish_post._publisher_router
    publisher = router.publisher_for_account(account)

    assert isinstance(publisher, WordPressPublisher)
    assert isinstance(
        publisher._tag_client,
        UrllibWordPressTagClient,
    )



def test_main_content_wires_wordpress_trash_controller(qtbot):
    content = MainContent()
    qtbot.addWidget(content)

    controller = (
        content.posts_page._remote_post_trashing_controller
    )

    assert controller is not None
    assert not controller.is_running


def test_main_content_trash_controller_uses_wordpress_trasher(qtbot):
    content = MainContent()
    qtbot.addWidget(content)

    controller = (
        content.posts_page._remote_post_trashing_controller
    )
    use_case = controller._trash_remote_post

    assert isinstance(use_case, TrashRemotePost)
    assert isinstance(
        use_case._trasher,
        WordPressPostTrasher,
    )

def test_main_content_wires_facebook_publisher(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    account = Account(
        name="Facebook Page Test",
        destination=PublishingDestination.FACEBOOK,
    )

    router = (
        content.posts_page
        ._publishing_controller
        ._publish_post
        ._publisher_router
    )

    publisher = router.publisher_for_account(account)

    assert isinstance(publisher, FacebookPublisher)
    assert isinstance(
        publisher._publishing_service,
        FacebookPublishingService,
    )
    assert isinstance(
        publisher._publishing_service._client,
        FacebookGraphClient,
    )

# qtbot ensures QApplication exists before MainContent constructs widgets.
def test_main_content_does_not_recover_when_accounts_file_is_missing(
    qtbot,
    monkeypatch,
) -> None:
    assert qtbot is not None

    paths = AppPaths(data_directory())

    assert not paths.accounts_file.exists()

    account_id = AccountId(uuid4())
    key = f"facebook:{account_id}:page_access_token"

    journal = JsonPendingCredentialCleanupRepository(
        paths.pending_credential_cleanup_file
    )
    journal.add(key)

    deleted_keys = []

    def record_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        record_delete,
    )

    with pytest.raises(
        OSError,
        match="Account storage is missing",
    ):
        MainContent()

    assert deleted_keys == []
    assert journal.all() == (key,)

def test_main_content_recovers_orphaned_facebook_credentials_on_startup(
    qtbot,
    monkeypatch,
) -> None:
    paths = AppPaths(data_directory())

    # Existing account storage is required for safe recovery.
    paths.accounts_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.accounts_file.write_text(
        "[]",
        encoding="utf-8",
    )

    account_id = AccountId(uuid4())
    key = f"facebook:{account_id}:page_access_token"

    journal = JsonPendingCredentialCleanupRepository(
        paths.pending_credential_cleanup_file,
    )
    journal.add(key)

    deleted_keys: list[str] = []

    def record_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        record_delete,
    )

    content = MainContent()
    qtbot.addWidget(content)

    assert deleted_keys == [key]
    assert journal.all() == ()

def test_main_content_preserves_pending_cleanup_when_keyring_delete_fails(
    qtbot,
    monkeypatch,
) -> None:
    assert qtbot is not None

    paths = AppPaths(data_directory())

    paths.accounts_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.accounts_file.write_text(
        "[]",
        encoding="utf-8",
    )

    account_id = AccountId(uuid4())
    key = f"facebook:{account_id}:page_access_token"

    journal = JsonPendingCredentialCleanupRepository(
        paths.pending_credential_cleanup_file,
    )
    journal.add(key)

    deleted_keys: list[str] = []

    def fail_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)
        raise OSError("Simulated keyring deletion failure")

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        fail_delete,
    )

    with pytest.raises(
        CredentialStorageError,
        match="Could not securely delete account credentials",
    ):
        MainContent()

    assert deleted_keys == [key]
    assert journal.all() == (key,)

def test_main_content_preserves_credentials_when_account_storage_is_corrupt(
    qtbot,
    monkeypatch,
) -> None:
    assert qtbot is not None

    paths = AppPaths(data_directory())

    paths.accounts_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.accounts_file.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    account_id = AccountId(uuid4())
    key = f"facebook:{account_id}:page_access_token"

    journal = JsonPendingCredentialCleanupRepository(
        paths.pending_credential_cleanup_file,
    )
    journal.add(key)

    deleted_keys: list[str] = []

    def record_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        record_delete,
    )

    with pytest.raises(AccountStorageError):
        MainContent()

    assert deleted_keys == []
    assert journal.all() == (key,)

def test_main_content_does_not_delete_credentials_when_cleanup_journal_is_corrupt(
    qtbot,
    monkeypatch,
) -> None:
    assert qtbot is not None

    paths = AppPaths(data_directory())

    paths.accounts_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.accounts_file.write_text(
        "[]",
        encoding="utf-8",
    )

    paths.pending_credential_cleanup_file.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    deleted_keys: list[str] = []

    def record_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        record_delete,
    )

    with pytest.raises(ValueError):
        MainContent()

    assert deleted_keys == []
    assert (
        paths.pending_credential_cleanup_file.read_text(
            encoding="utf-8",
        )
        == "{invalid json"
    )

def test_main_content_preserves_credentials_for_existing_account(
    qtbot,
    monkeypatch,
) -> None:
    paths = AppPaths(data_directory())

    account = Account(
        name="Existing Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file,
    )
    account_repository.add(account)

    key = f"facebook:{account.id}:page_access_token"

    journal = JsonPendingCredentialCleanupRepository(
        paths.pending_credential_cleanup_file,
    )
    journal.add(key)

    deleted_keys: list[str] = []

    def record_delete(_store, credential_key: str) -> None:
        deleted_keys.append(credential_key)

    monkeypatch.setattr(
        "socialflow.infrastructure.credentials.keyring_credential_store."
        "KeyringCredentialStore.delete",
        record_delete,
    )

    content = MainContent()
    qtbot.addWidget(content)

    assert deleted_keys == []
    assert account_repository.all() == (account,)
    assert journal.all() == ()