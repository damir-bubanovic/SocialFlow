from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.services.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.modules.wordpress.adapters.wordpress_tag_creation_service import (
    WordPressTagCreationService,
)
from socialflow.modules.posts.services.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.modules.posts.services.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.modules.posts.services.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.modules.posts.services.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.modules.posts.services.list_remote_posts import (
    ListRemotePosts,
)
from socialflow.modules.posts.services.list_trashed_remote_posts import (
    ListTrashedRemotePosts,
)
from socialflow.modules.posts.services.restore_remote_post import (
    RestoreRemotePost,
)
from socialflow.modules.posts.controllers.wordpress_category_creation_controller import (
    WordPressCategoryCreationController,
)
from socialflow.modules.posts.services.publish_post import PublishPost
from socialflow.modules.posts.services.publisher_router import PublisherRouter
from socialflow.modules.posts.services.unconfigured_publisher import (
    UnconfiguredPublisher,
)
from socialflow.modules.posts.services.create_tag import CreateTag
from socialflow.modules.posts.services.list_tags import ListTags
from socialflow.modules.posts.services.null_tag_provider import NullTagProvider
from socialflow.modules.posts.services.routing_tag_provider import (
    RoutingTagProvider,
)
from socialflow.modules.wordpress.adapters.wordpress_tag_provider import (
    WordPressTagProvider,
)
from socialflow.modules.wordpress.adapters.wordpress_category_provider import (
    WordPressCategoryProvider,
)
from socialflow.modules.wordpress.api.urllib_wordpress_category_client import (
    UrllibWordPressCategoryClient,
)
from socialflow.modules.posts.services.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.modules.wordpress.api.urllib_wordpress_tag_client import (
    UrllibWordPressTagClient,
)
from socialflow.core.destination import (
    PublishingDestination,
)
from socialflow.modules.accounts.repositories.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.infrastructure.credentials.keyring_credential_store import (
    KeyringCredentialStore,
)
from socialflow.modules.posts.repositories.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.modules.posts.services.uuid_publication_id_generator import (
    UuidPublicationIdGenerator,
)
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.infrastructure.time.system_clock import SystemClock
from socialflow.modules.wordpress.auth.wordpress_connection_verifier_factory import (
    WordPressConnectionVerifierFactory,
)
from socialflow.modules.accounts.views.accounts_page import AccountsPage
from socialflow.ui.navigation import Navigation
from socialflow.modules.posts.views.posts_page import PostsPage
from socialflow.modules.accounts.services.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)
from socialflow.modules.wordpress.adapters.wordpress_publisher import (
    WordPressPublisher,
)
from socialflow.modules.wordpress.api.urllib_wordpress_post_client import (
    UrllibWordPressPostClient,
)
from socialflow.modules.wordpress.mappers.wordpress_post_parser import (
    WordPressPostParser,
)
from socialflow.modules.wordpress.adapters.wordpress_post_retriever import (
    WordPressPostRetriever,
)
from socialflow.modules.wordpress.adapters.wordpress_post_provider import (
    WordPressPostProvider,
)
from socialflow.modules.posts.services.update_remote_post import (
    UpdateRemotePost,
)
from socialflow.modules.posts.services.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.modules.wordpress.adapters.wordpress_post_trasher import (
    WordPressPostTrasher,
)
from socialflow.modules.wordpress.adapters.wordpress_post_restorer import (
    WordPressPostRestorer,
)
from socialflow.modules.wordpress.adapters.wordpress_post_updater import (
    WordPressPostUpdater,
)
from socialflow.modules.posts.controllers.wordpress_tag_preparation_controller import (
    WordPressTagPreparationController,
)
from socialflow.modules.posts.controllers.wordpress_tag_creation_controller import (
    WordPressTagCreationController,
)
from socialflow.modules.posts.services.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.modules.posts.services.list_remote_media import (
    ListRemoteMedia,
)
from socialflow.modules.wordpress.adapters.wordpress_media_provider import (
    WordPressMediaProvider,
)
from socialflow.modules.accounts.services.get_wordpress_credentials import (
    GetWordPressCredentials,
)
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.services.facebook_connection_verifier import (
    FacebookConnectionVerifier,
)
from socialflow.modules.facebook.services.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.facebook.services.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.application.credentials.pending_cleanup_guarded_credential_store import (
    PendingCleanupGuardedCredentialStore,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)
from socialflow.modules.accounts.services.remove_account_with_credential_cleanup import (
    RemoveAccountWithCredentialCleanup,
)


class MainContent(QWidget):
    """Primary content area of the SocialFlow main window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.navigation = Navigation(self)

        # Persistent paths and pending credential cleanup journal.
        paths = AppPaths(data_directory())

        cleanup_repository = JsonPendingCredentialCleanupRepository(
            paths.pending_credential_cleanup_file,
        )

        # Shared secure credential storage.
        credential_store = KeyringCredentialStore()

        guarded_credential_store = PendingCleanupGuardedCredentialStore(
            credential_store=credential_store,
            cleanup_repository=cleanup_repository,
        )

        save_wordpress_credentials = SaveWordPressCredentials(
            credential_store=guarded_credential_store,
        )
        get_wordpress_credentials = GetWordPressCredentials(
            credential_store=credential_store,
        )
        delete_wordpress_credentials = DeleteWordPressCredentials(
            credential_store=credential_store,
        )
        # Facebook Page credentials use the existing shared keyring store.
        save_facebook_credentials = SaveFacebookCredentials(
            credential_store=guarded_credential_store,
        )
        get_facebook_credentials = GetFacebookCredentials(
            credential_store=credential_store,
        )
        delete_facebook_credentials = DeleteFacebookCredentials(
            credential_store=credential_store,
        )
        # Facebook Graph API services.
        facebook_graph_client = FacebookGraphClient(
            api_version="v24.0",
        )

        facebook_page_discovery_service = FacebookPageDiscoveryService(
            client=facebook_graph_client,
        )
        facebook_publishing_service = FacebookPublishingService(
            client=facebook_graph_client,
        )

        self.wordpress_connection_verifier = (
            WordPressConnectionVerifierFactory.create(
                credential_store=credential_store,
            )
        )

        self.facebook_connection_verifier = FacebookConnectionVerifier(
            credential_store=credential_store,
            graph_client=facebook_graph_client,
        )

        # Persistent application storage.
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

        remove_account_with_credential_cleanup = (
            RemoveAccountWithCredentialCleanup(
                remove_account=remove_account,
                account_repository=account_repository,
                cleanup_repository=cleanup_repository,
                credential_store=credential_store,
            )
        )

        # Recover credentials left pending after interrupted account removal.
        # Never interpret missing account storage as proof of removal.
        pending_cleanup = cleanup_repository.all()

        if pending_cleanup and not paths.accounts_file.exists():
            raise OSError(
                "Account storage is missing; credential recovery aborted."
            )

        # Recovery failures abort initialization rather than risking data loss.
        remove_account_with_credential_cleanup.recover_pending()

        update_account = UpdateAccount(account_repository)


        # Tag services.
        wordpress_tag_client = UrllibWordPressTagClient()

        wordpress_tag_creation_service = WordPressTagCreationService(
            tag_client=wordpress_tag_client,
            credential_store=credential_store,
        )

        wordpress_tag_provider = WordPressTagProvider(
            tag_client=wordpress_tag_client,
            credential_store=credential_store,
        )

        tag_provider = RoutingTagProvider(
            providers={
                PublishingDestination.WORDPRESS: wordpress_tag_provider,
            },
            fallback=NullTagProvider(),
        )

        list_tags = ListTags(tag_provider)
        create_tag = CreateTag(tag_provider)
        list_remote_tags = ListRemoteTags(wordpress_tag_provider)

        wordpress_category_client = UrllibWordPressCategoryClient()
        wordpress_category_provider = WordPressCategoryProvider(
            category_client=wordpress_category_client,
            credential_store=credential_store,
        )
        list_remote_categories = ListRemoteCategories(
            wordpress_category_provider
        )


        # Publishing services.
        publisher = UnconfiguredPublisher()

        wordpress_post_client = UrllibWordPressPostClient()

        wordpress_post_retriever = WordPressPostRetriever(
            client=wordpress_post_client,
            parser=WordPressPostParser(),
        )

        wordpress_post_provider = WordPressPostProvider(
            retriever=wordpress_post_retriever,
            credential_store=credential_store,
        )

        list_remote_posts = ListRemotePosts(
            provider=wordpress_post_provider,
        )

        list_trashed_remote_posts = ListTrashedRemotePosts(
            provider=wordpress_post_provider,
        )
        wordpress_media_provider = WordPressMediaProvider(
            client=wordpress_post_client,
            credential_store=credential_store,
        )

        list_remote_media = ListRemoteMedia(
            provider=wordpress_media_provider,
        )
        wordpress_post_updater = WordPressPostUpdater(
            client=wordpress_post_client,
            credential_store=credential_store,
        )

        update_remote_post = UpdateRemotePost(
            updater=wordpress_post_updater,
        )

        wordpress_post_trasher = WordPressPostTrasher(
            client=wordpress_post_client,
            credential_store=credential_store,
        )

        trash_remote_post = TrashRemotePost(
            trasher=wordpress_post_trasher,
        )

        wordpress_post_restorer = WordPressPostRestorer(
            client=wordpress_post_client,
            credential_store=credential_store,
        )

        restore_remote_post = RestoreRemotePost(
            restorer=wordpress_post_restorer,
        )

        publisher_router = PublisherRouter(
            publishers={
                PublishingDestination.FACEBOOK: publisher,
                PublishingDestination.INSTAGRAM: publisher,
                PublishingDestination.WORDPRESS: publisher,
            },
            account_factories={
                PublishingDestination.FACEBOOK: (
                    lambda account: FacebookPublisher(
                        account=account,
                        credential_store=credential_store,
                        publishing_service=facebook_publishing_service,
                    )
                ),
                PublishingDestination.WORDPRESS: (
                    lambda account: WordPressPublisher(
                        account=account,
                        credential_store=credential_store,
                        post_client=wordpress_post_client,
                        tag_client=wordpress_tag_client,
                    )
                ),
            },
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
            list_remote_posts=list_remote_posts,
            update_remote_post=update_remote_post,
            trash_remote_post=trash_remote_post,
            list_trashed_remote_posts=list_trashed_remote_posts,
            restore_remote_post=restore_remote_post,
            wordpress_tag_preparation_controller=WordPressTagPreparationController(
                tag_creation_service=wordpress_tag_creation_service,
            ),
            wordpress_tag_creation_controller=WordPressTagCreationController(
                tag_creation_service=wordpress_tag_creation_service,
            ),
            list_remote_tags=list_remote_tags,
            list_remote_categories=list_remote_categories,
            wordpress_category_creation_controller=(
                WordPressCategoryCreationController(
                    category_provider=wordpress_category_provider,
                )
            ),
            list_remote_media=list_remote_media,
        )

        # Accounts page with WordPress and Facebook credential management.
        self.accounts_page = AccountsPage(
            add_account=add_account,
            list_accounts=list_accounts,
            remove_account=remove_account,
            update_account=update_account,
            remove_account_with_credential_cleanup=(
                remove_account_with_credential_cleanup
            ),
            parent=self,
            wordpress_connection_verifier=self.wordpress_connection_verifier,
            facebook_connection_verifier=self.facebook_connection_verifier,
            save_wordpress_credentials=save_wordpress_credentials,
            delete_wordpress_credentials=delete_wordpress_credentials,
            get_wordpress_credentials=get_wordpress_credentials,
            save_facebook_credentials=save_facebook_credentials,
            get_facebook_credentials=get_facebook_credentials,
            delete_facebook_credentials=delete_facebook_credentials,
            facebook_page_discovery_service=facebook_page_discovery_service,
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
