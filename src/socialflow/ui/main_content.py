from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.application.accounts.update_account import UpdateAccount
from socialflow.application.publishing.null_publisher import NullPublisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.ui.accounts.accounts_page import AccountsPage
from socialflow.ui.navigation import Navigation
from socialflow.ui.posts.posts_page import PostsPage


class MainContent(QWidget):
    """Primary content area of the SocialFlow main window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.navigation = Navigation(self)

        paths = AppPaths(data_directory())
        account_repository = JsonAccountRepository(paths.accounts_file)

        add_account = AddAccount(account_repository)
        list_accounts = ListAccounts(account_repository)
        remove_account = RemoveAccount(account_repository)
        update_account = UpdateAccount(account_repository)

        publisher = NullPublisher()
        publisher_router = PublisherRouter(
            {
                PublishingDestination.FACEBOOK: publisher,
                PublishingDestination.INSTAGRAM: publisher,
                PublishingDestination.WORDPRESS: publisher,
            }
        )
        publish_post = PublishPost(publisher_router)

        self.posts_page = PostsPage(
            publish_post=publish_post,
            list_accounts=list_accounts,
            parent=self,
        )

        self.accounts_page = AccountsPage(
            add_account=add_account,
            list_accounts=list_accounts,
            remove_account=remove_account,
            update_account=update_account,
            parent=self,
        )

        self.accounts_page.accounts_changed.connect(
            self.posts_page.refresh_accounts
        )

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