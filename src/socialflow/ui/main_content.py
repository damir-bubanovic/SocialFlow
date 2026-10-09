
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.application.accounts.update_account import UpdateAccount
from socialflow.application.credentials.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.application.images.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.application.images.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.application.publishing.unconfigured_publisher import (
    UnconfiguredPublisher,
)
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.application.tags.null_tag_provider import NullTagProvider
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.accounts.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.infrastructure.credentials.keyring_credential_store import (
    KeyringCredentialStore,
)
from socialflow.infrastructure.publishing.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.infrastructure.publishing.uuid_publication_id_generator import (
    UuidPublicationIdGenerator,
)
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.infrastructure.time.system_clock import SystemClock
from socialflow.infrastructure.wordpress.wordpress_connection_verifier_factory import (
    WordPressConnectionVerifierFactory,
)
from socialflow.ui.accounts.accounts_page import AccountsPage
from socialflow.ui.navigation import Navigation
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.application.credentials.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)


class MainContent(QWidget):
    """Primary content area of the SocialFlow main window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.navigation = Navigation(self)

        # Shared credential storage for WordPress connections.
        credential_store = KeyringCredentialStore()

        save_wordpress_credentials = SaveWordPressCredentials(
            credential_store=credential_store,
        )
        delete_wordpress_credentials = DeleteWordPressCredentials(
            credential_store=credential_store,
        )

        self.wordpress_connection_verifier = (
            WordPressConnectionVerifierFactory.create(
                credential_store=credential_store,
            )
        )

        # Persistent application storage.
        paths = AppPaths(data_directory())

        account_repository = JsonAccountRepository(
            paths.accounts_file
        )

        publication_repository = JsonPublicationRepository(
            paths.publications_file,
            account_repository=account_repository,
        )
        publication_repository.migrate_legacy_records()

        list_recent_publications = ListRecentPublications(
            publication_repository
        )

        clock = SystemClock()

        # Account management services.
        add_account = AddAccount(account_repository)
        list_accounts = ListAccounts(account_repository)
        remove_account = RemoveAccount(account_repository)
        update_account = UpdateAccount(account_repository)

        # Tag services.
        tag_provider = NullTagProvider()
        list_tags = ListTags(tag_provider)
        create_tag = CreateTag(tag_provider)

        # Publishing services.
        publisher = UnconfiguredPublisher()

        publisher_router = PublisherRouter(
            {
                PublishingDestination.FACEBOOK: publisher,
                PublishingDestination.INSTAGRAM: publisher,
                PublishingDestination.WORDPRESS: publisher,
            }
        )

        # Image preparation services.
        image_profile_provider = ImageProfileProvider(
            profiles=DEFAULT_IMAGE_PROFILES,
        )

        image_preparation_service = ImagePreparationService(
            profile_provider=image_profile_provider,
        )

        publish_post = PublishPost(
            publisher_router=publisher_router,
            publication_id_generator=UuidPublicationIdGenerator(),
            image_preparation_service=image_preparation_service,
            image_output_directory=paths.prepared_images_directory,
            publication_repository=publication_repository,
            clock=clock,
        )

        # Posts page.
        self.posts_page = PostsPage(
            publish_post=publish_post,
            list_accounts=list_accounts,
            list_tags=list_tags,
            create_tag=create_tag,
            list_recent_publications=list_recent_publications,
            parent=self,
        )

        # Accounts page with WordPress credential management.
        self.accounts_page = AccountsPage(
            add_account=add_account,
            list_accounts=list_accounts,
            remove_account=remove_account,
            update_account=update_account,
            parent=self,
            wordpress_connection_verifier=self.wordpress_connection_verifier,
            save_wordpress_credentials=save_wordpress_credentials,
            delete_wordpress_credentials=delete_wordpress_credentials,
        )

        self.accounts_page.accounts_changed.connect(
            self.posts_page.refresh_accounts
        )

        # Main application pages.
        self.pages = QStackedWidget(self)
        self.pages.addWidget(self.posts_page)
        self.pages.addWidget(self.accounts_page)

        layout = QVBoxLayout()
        layout.addWidget(self.navigation)
        layout.addWidget(self.pages)

        self.setLayout(layout)

        self.navigation.tab_bar.currentChanged.connect(
            self._show_selected_page
        )

    def _show_selected_page(self, index: int) -> None:
        """Display the page selected in the primary navigation."""
        if index == Navigation.POSTS_INDEX:
            self.pages.setCurrentWidget(self.posts_page)
        elif index == Navigation.ACCOUNTS_INDEX:
            self.pages.setCurrentWidget(self.accounts_page)
