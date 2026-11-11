from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.repositories.errors import (
    AccountStorageError,
)
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.services.update_account_with_instagram_cleanup import (
    InstagramConversionCleanupIncompleteError,
    UpdateAccountWithInstagramCleanup,
)
from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)
from socialflow.modules.accounts.services.get_wordpress_credentials import (
    GetWordPressCredentials,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import (
    PublishingDestination,
)
from socialflow.modules.accounts.views.account_form import AccountForm
from socialflow.modules.accounts.views.account_list import AccountList
from socialflow.modules.accounts.views.account_status import AccountStatus
from socialflow.modules.accounts.controllers.wordpress_verification_controller import (
    WordPressVerificationController,
)
from socialflow.modules.accounts.controllers.facebook_verification_controller import (
    FacebookVerificationController,
)
from socialflow.modules.accounts.controllers.instagram_verification_controller import (
    InstagramVerificationController,
)
from socialflow.modules.accounts.controllers.facebook_page_discovery_controller import (
    FacebookPageDiscoveryController,
)
from socialflow.modules.facebook.services.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.accounts.services.save_instagram_credentials import (
    SaveInstagramCredentials,
)
from socialflow.modules.accounts.services.get_instagram_credentials import (
    GetInstagramCredentials,
)
from socialflow.modules.accounts.services.delete_instagram_credentials import (
    DeleteInstagramCredentials,
)
from socialflow.modules.accounts.services.remove_account_with_credential_cleanup import (
    RemoveAccountWithCredentialCleanup,
)
from socialflow.modules.accounts.services.errors import (
    AccountCredentialCleanupIncompleteError,
)


class AccountsPage(QWidget):
    """Page for managing publishing accounts."""

    accounts_changed = Signal()
    verification_finished = Signal()

    def __init__(
        self,
        add_account: AddAccount,
        list_accounts: ListAccounts,
        remove_account: RemoveAccount,
        update_account: UpdateAccount,
        parent: QWidget | None = None,
        wordpress_connection_verifier: ConnectionVerifier | None = None,
        save_wordpress_credentials: SaveWordPressCredentials | None = None,
        delete_wordpress_credentials: DeleteWordPressCredentials | None = None,
        get_wordpress_credentials: GetWordPressCredentials | None = None,
        facebook_page_discovery_service: FacebookPageDiscoveryService | None = None,
        save_facebook_credentials: SaveFacebookCredentials | None = None,
        delete_facebook_credentials: DeleteFacebookCredentials | None = None,
        get_facebook_credentials: GetFacebookCredentials | None = None,
        facebook_connection_verifier: ConnectionVerifier | None = None,
        remove_account_with_credential_cleanup: (
                RemoveAccountWithCredentialCleanup | None
        ) = None,
        instagram_connection_verifier: ConnectionVerifier | None = None,
        save_instagram_credentials: SaveInstagramCredentials | None = None,
        get_instagram_credentials: GetInstagramCredentials | None = None,
        delete_instagram_credentials: DeleteInstagramCredentials | None = None,
        update_account_with_instagram_cleanup: (
                UpdateAccountWithInstagramCleanup | None
        ) = None,
    ) -> None:
        super().__init__(parent)

        self._add_account = add_account
        self._list_accounts = list_accounts
        self._remove_account = remove_account
        self._remove_account_with_credential_cleanup = (
            remove_account_with_credential_cleanup
        )
        self._update_account = update_account
        self._wordpress_connection_verifier = wordpress_connection_verifier
        self._save_wordpress_credentials = save_wordpress_credentials
        self._delete_wordpress_credentials = delete_wordpress_credentials
        self._get_wordpress_credentials = get_wordpress_credentials
        self._save_facebook_credentials = save_facebook_credentials
        self._delete_facebook_credentials = delete_facebook_credentials
        self._get_facebook_credentials = get_facebook_credentials
        self._save_instagram_credentials = save_instagram_credentials
        self._get_instagram_credentials = get_instagram_credentials
        self._delete_instagram_credentials = delete_instagram_credentials
        self._update_account_with_instagram_cleanup = (
            update_account_with_instagram_cleanup
        )
        self._verification_controller = (
            WordPressVerificationController(
                wordpress_connection_verifier,
                parent=self,
            )
            if wordpress_connection_verifier is not None
            else None
        )

        self._facebook_verification_controller = (
            FacebookVerificationController(
                facebook_connection_verifier,
                parent=self,
            )
            if facebook_connection_verifier is not None
            else None
        )

        self._instagram_verification_controller = (
            InstagramVerificationController(
                instagram_connection_verifier,
                parent=self,
            )
            if instagram_connection_verifier is not None
            else None
        )

        self._facebook_discovery_controller = (
            FacebookPageDiscoveryController(
                facebook_page_discovery_service,
                parent=self,
            )
            if facebook_page_discovery_service is not None
            else None
        )
        self._facebook_discovery_context: tuple | None = None
        self._facebook_discovery_generation = 0
        self.account_form = AccountForm(self)
        self.account_list = AccountList(self)
        self.account_status = AccountStatus(self)

        self.update_button = QPushButton("Save changes", self)
        self.update_button.setEnabled(False)

        self.remove_button = QPushButton("Remove account", self)
        self.remove_button.setEnabled(False)

        self.verify_button = QPushButton("Verify connection", self)
        self.verify_button.setEnabled(False)

        # Left panel: account selection.
        self.accounts_panel = QWidget(self)
        accounts_layout = QVBoxLayout(self.accounts_panel)
        accounts_layout.setContentsMargins(12, 12, 12, 12)
        accounts_layout.setSpacing(10)

        self.accounts_heading = QLabel("Accounts", self.accounts_panel)
        self.accounts_heading.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )

        accounts_layout.addWidget(self.accounts_heading)
        accounts_layout.addWidget(self.account_list, 1)

        self.new_account_button = QPushButton(
            "+ New account",
            self.accounts_panel,
        )
        accounts_layout.addWidget(self.new_account_button)

        # Right panel: selected account details and actions.
        self.details_panel = QWidget(self)
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(16, 12, 16, 12)
        details_layout.setSpacing(12)

        self.details_heading = QLabel(
            "Account details",
            self.details_panel,
        )
        self.details_heading.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )

        details_layout.addWidget(self.details_heading)
        details_layout.addWidget(self.account_form)

        # Connection verification stays close to the credentials.
        details_layout.addWidget(self.verify_button)
        details_layout.addWidget(self.account_status)

        # Unused vertical space remains below the account information.
        details_layout.addStretch(1)

        # Account management actions.
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.update_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.remove_button.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        actions_layout.addWidget(self.update_button, 1)
        actions_layout.addWidget(self.remove_button)

        details_layout.addLayout(actions_layout)

        # Resizable master-detail layout.
        self.accounts_splitter = QSplitter(
            Qt.Orientation.Horizontal,
            self,
        )
        self.accounts_splitter.setChildrenCollapsible(False)
        self.accounts_splitter.setHandleWidth(6)

        self.accounts_splitter.addWidget(self.accounts_panel)
        self.accounts_splitter.addWidget(self.details_panel)

        self.accounts_splitter.setStretchFactor(0, 35)
        self.accounts_splitter.setStretchFactor(1, 65)

        self.accounts_panel.setMinimumWidth(220)
        self.details_panel.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.accounts_splitter)

        self.accounts_splitter.setSizes([350, 650])

        self.new_account_button.clicked.connect(
            self._enter_new_account_mode
        )
        self.account_form.add_button.clicked.connect(
            self._handle_add_account
        )
        self.update_button.clicked.connect(
            self._handle_update_account
        )
        self.remove_button.clicked.connect(
            self._handle_remove_account
        )
        self.verify_button.clicked.connect(
            self._handle_verify_connection
        )
        self.account_list.itemSelectionChanged.connect(
            self._handle_account_selection_changed
        )

        if self._verification_controller is not None:
            self._verification_controller.result_ready.connect(
                self.account_status.show_connection_result
            )
            self._verification_controller.error_occurred.connect(
                self.account_status.show_connection_error
            )
            self._verification_controller.finished.connect(
                self._update_account_buttons
            )
            self._verification_controller.finished.connect(
                self.verification_finished.emit
            )

        if self._facebook_verification_controller is not None:
            controller = self._facebook_verification_controller
            controller.result_ready.connect(
                self.account_status.show_connection_result
            )
            controller.error_occurred.connect(
                self.account_status.show_connection_error
            )
            controller.finished.connect(
                self._update_account_buttons
            )
            controller.finished.connect(
                self.verification_finished.emit
            )

        if self._instagram_verification_controller is not None:
            controller = self._instagram_verification_controller
            controller.result_ready.connect(
                self.account_status.show_connection_result
            )
            controller.error_occurred.connect(
                self.account_status.show_connection_error
            )
            controller.finished.connect(
                self._update_account_buttons
            )
            controller.finished.connect(
                self.verification_finished.emit
            )

        self.account_form.facebook_discovery_requested.connect(
            self._handle_facebook_discovery_requested
        )
        self.account_form.destination_input.currentIndexChanged.connect(
            self._invalidate_facebook_discovery
        )

        if self._facebook_discovery_controller is not None:
            self._facebook_discovery_controller.result_ready.connect(
                self._handle_facebook_pages_discovered
            )
            self._facebook_discovery_controller.error_occurred.connect(
                self._handle_facebook_discovery_error
            )
            self._facebook_discovery_controller.finished.connect(
                self._handle_facebook_discovery_finished
            )

        self._refresh_accounts()


    def _current_facebook_discovery_context(self) -> tuple:
        """Identify the account and form context for discovery."""
        account = self.account_list.selected_account()

        return (
            account.id if account is not None else None,
            self.account_form.selected_destination(),
            self._facebook_discovery_generation,
        )

    def _invalidate_facebook_discovery(self, *_args) -> None:
        """Invalidate results from an earlier form context."""
        self._facebook_discovery_generation += 1
        self._facebook_discovery_context = None
        self.account_form.clear_discovered_facebook_pages()

        controller = self._facebook_discovery_controller
        if controller is not None and controller.is_running:
            self.account_form.set_facebook_discovery_running(True)


    def _handle_facebook_discovery_requested(
        self,
        user_access_token: str,
    ) -> None:
        """Start Facebook Page discovery outside the UI thread."""
        controller = self._facebook_discovery_controller

        if controller is None:
            self.account_form.set_facebook_discovery_running(False)
            self.account_status.show_error()
            return

        if controller.is_running:
            self.account_form.set_facebook_discovery_running(True)
            return

        self._facebook_discovery_context = (
            self._current_facebook_discovery_context()
        )

        controller.start(user_access_token)

    def _handle_facebook_pages_discovered(self, pages: list) -> None:
        """Display Pages only for the originating form context."""
        if self._facebook_discovery_context is None:
            return

        if (
                self._facebook_discovery_context
                != self._current_facebook_discovery_context()
        ):
            return

        if (
                self.account_form.selected_destination()
                != PublishingDestination.FACEBOOK
        ):
            return

        self.account_form.set_discovered_facebook_pages(pages)

    def _handle_facebook_discovery_error(self, message: str) -> None:
        """Report errors only for the originating form context."""
        if self._facebook_discovery_context is None:
            return

        if (
                self._facebook_discovery_context
                != self._current_facebook_discovery_context()
        ):
            return

        self.account_status.show_connection_error(message)

    def _handle_facebook_discovery_finished(self) -> None:
        """Clear request context and restore discovery controls."""
        self._facebook_discovery_context = None
        self.account_form.set_facebook_discovery_running(False)

    def _enter_new_account_mode(self) -> None:
        """Show a blank form for creating an account."""
        self._invalidate_facebook_discovery()
        self.account_list.clearSelection()
        self.account_list.setCurrentRow(-1)
        self.account_form.clear()

        self.details_heading.setText("New account")
        self.account_form.add_button.setVisible(True)
        self.update_button.setVisible(False)
        self.remove_button.setVisible(False)
        self.verify_button.setVisible(False)

        self._update_account_buttons()

    def _enter_edit_account_mode(self) -> None:
        """Show the selected account and its available actions."""
        self._invalidate_facebook_discovery()
        account = self.account_list.selected_account()

        if account is None:
            self._enter_new_account_mode()
            return

        self.details_heading.setText("Edit account")
        self.account_form.add_button.setVisible(False)
        self.update_button.setVisible(True)
        self.remove_button.setVisible(True)
        self.verify_button.setVisible(True)

        self._load_selected_account()
        self._update_account_buttons()

    def _handle_account_selection_changed(self) -> None:
        """Switch modes when the account selection changes."""
        if self.account_list.selected_account() is None:
            self._enter_new_account_mode()
        else:
            self._enter_edit_account_mode()

    def _save_selected_facebook_page_token(
        self,
        account: Account,
    ) -> None:
        """Store a selected Facebook Page token securely."""
        if account.destination != PublishingDestination.FACEBOOK:
            return

        token = self.account_form.selected_facebook_page_token()
        if not token:
            return

        service = self._save_facebook_credentials
        if service is None:
            raise CredentialStorageError(
                "Secure Facebook credential storage is unavailable."
            )

        service.execute(account, token)

    def _save_instagram_access_token(
        self,
        account: Account,
        access_token: str,
    ) -> bool:
        """Save a supplied Instagram token securely."""
        if account.destination != PublishingDestination.INSTAGRAM:
            return False

        if not access_token.strip():
            return False

        service = self._save_instagram_credentials
        if service is None:
            raise CredentialStorageError(
                "Secure Instagram credential storage is unavailable."
            )

        return service.execute(account, access_token)

    def _handle_add_account(self) -> None:
        """Add an account and then save its WordPress credentials."""
        if self.account_form.selected_destination() is None:
            self.account_status.show_error()
            return

        account = self.account_form.account()
        password = self.account_form.wordpress_application_password()
        instagram_token = self.account_form.instagram_access_token()
        self.account_form.instagram_access_token_input.clear()

        try:
            self._add_account.execute(account)
        except (DuplicateAccountError, InvalidAccountError):
            self.account_status.show_error()
            return

        if (
            account.destination == PublishingDestination.WORDPRESS
            and self._save_wordpress_credentials is not None
        ):
            try:
                self._save_wordpress_credentials.execute(
                    account,
                    password,
                )
            except CredentialStorageError:
                # Account creation succeeded, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        if account.destination == PublishingDestination.FACEBOOK:
            try:
                self._save_selected_facebook_page_token(account)
            except CredentialStorageError:
                # Attempt to roll back account creation when the
                # Facebook Page token could not be saved.
                try:
                    self._remove_account.execute(account)
                except AccountNotFoundError:
                    # The account is already absent.
                    pass
                except (AccountStorageError, OSError):
                    # Rollback failed. The account may still exist.
                    pass

                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        if account.destination == PublishingDestination.INSTAGRAM:
            try:
                self._save_instagram_access_token(
                    account,
                    instagram_token,
                )
            except CredentialStorageError:
                # The account exists, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_success()
        self.accounts_changed.emit()

    def _handle_update_account(self) -> None:
        """Update an account and manage its WordPress credentials."""
        current = self.account_list.selected_account()

        if current is None:
            return

        updated = self.account_form.account()
        password = self.account_form.wordpress_application_password()
        instagram_token = self.account_form.instagram_access_token()
        self.account_form.instagram_access_token_input.clear()

        if (
                current.destination == PublishingDestination.FACEBOOK
                and updated.destination == PublishingDestination.FACEBOOK
        ):
            old_page_id = (
                current.facebook_config.page_id
                if current.facebook_config is not None
                else ""
            )
            new_page_id = (
                updated.facebook_config.page_id
                if updated.facebook_config is not None
                else ""
            )

            if (
                    old_page_id != new_page_id
                    and not self.account_form.selected_facebook_page_token()
            ):
                if self._get_facebook_credentials is not None:
                    try:
                        existing_token = (
                            self._get_facebook_credentials.execute(current)
                        )
                    except CredentialStorageError:
                        self.account_status.show_error()
                        return

                    if (
                            existing_token
                            and self._delete_facebook_credentials is None
                    ):
                        self.account_status.show_error()
                        return

        # Preserve the old token so it can be restored if updating fails.
        previous_facebook_token: str | None = None
        old_facebook_token_deleted = False
        replacement_facebook_token_saved = False
        facebook_account: Account | None = None

        if (
                current.destination == PublishingDestination.FACEBOOK
                and updated.destination == PublishingDestination.FACEBOOK
                and current.facebook_config is not None
                and updated.facebook_config is not None
                and (
                current.facebook_config.page_id
                != updated.facebook_config.page_id
        )
                and not self.account_form.selected_facebook_page_token()
                and self._delete_facebook_credentials is not None
        ):
            if (
                    self._get_facebook_credentials is None
                    or self._save_facebook_credentials is None
            ):
                self.account_status.show_error()
                return

            try:
                previous_facebook_token = (
                    self._get_facebook_credentials.execute(current)
                )

                self._delete_facebook_credentials.execute(current)
                old_facebook_token_deleted = True

            except CredentialStorageError:
                self.account_status.show_error()
                return

        # Save a selected replacement Page token before updating the account.
        if updated.destination == PublishingDestination.FACEBOOK:
            selected_token = (
                self.account_form.selected_facebook_page_token()
            )

            if selected_token:
                if current.destination == PublishingDestination.FACEBOOK:
                    if (
                            self._get_facebook_credentials is None
                            or self._delete_facebook_credentials is None
                    ):
                        self.account_status.show_error()
                        return

                    try:
                        previous_facebook_token = (
                            self._get_facebook_credentials.execute(current)
                        )
                    except CredentialStorageError:
                        self.account_status.show_error()
                        return

                facebook_account = Account(
                    name=updated.name.strip(),
                    destination=updated.destination,
                    id=current.id,
                    facebook_config=updated.facebook_config,
                )

                try:
                    self._save_selected_facebook_page_token(
                        facebook_account
                    )
                    replacement_facebook_token_saved = True
                except CredentialStorageError:
                    self.account_status.show_error()
                    return

        try:
            if (
                    current.destination == PublishingDestination.INSTAGRAM
                    and updated.destination != PublishingDestination.INSTAGRAM
                    and self._update_account_with_instagram_cleanup is not None
            ):
                self._update_account_with_instagram_cleanup.execute(
                    current,
                    updated,
                )
            else:
                self._update_account.execute(
                    current,
                    updated,
                )
        except InstagramConversionCleanupIncompleteError:
            # Account metadata was updated, but the obsolete Instagram token
            # still requires cleanup. Startup recovery will retry it.
            self._refresh_accounts()
            self.account_status.show_error()
            self.accounts_changed.emit()
            return


        except (

                AccountNotFoundError,

                DuplicateAccountError,

                InvalidAccountError,

                AccountStorageError,

                OSError,

        ):

            # An update error does not necessarily mean the account

            # metadata was left unchanged. Verify persisted state

            # before rolling back a replacement Facebook credential.

            if replacement_facebook_token_saved:

                try:

                    persisted_accounts = self._list_accounts.execute()

                except (AccountStorageError, OSError):

                    # Without a reliable persisted state, deleting the

                    # replacement token could destroy a valid credential.

                    self.account_status.show_error()

                    return

                persisted_account = next(

                    (

                        account

                        for account in persisted_accounts

                        if account.id == current.id

                    ),

                    None,

                )

                if persisted_account is None:
                    self.account_status.show_error()

                    return

                if persisted_account.destination != current.destination:
                    # The conversion may have persisted despite the

                    # exception. Keep the replacement Facebook token.

                    self._refresh_accounts()

                    self.account_status.show_error()

                    self.accounts_changed.emit()

                    return

            if replacement_facebook_token_saved:
                try:
                    if previous_facebook_token is not None:
                        if self._save_facebook_credentials is None:
                            self.account_status.show_error()
                            return

                        self._save_facebook_credentials.execute(
                            current,
                            previous_facebook_token,
                        )
                    elif (
                            self._delete_facebook_credentials is not None
                            and facebook_account is not None
                        ):
                        self._delete_facebook_credentials.execute(
                            facebook_account
                        )

                except CredentialStorageError:
                    self.account_status.show_error()
                    return

            elif old_facebook_token_deleted and previous_facebook_token:
                if self._save_facebook_credentials is None:
                    self.account_status.show_error()
                    return

                try:
                    self._save_facebook_credentials.execute(
                        current,
                        previous_facebook_token,
                    )
                except CredentialStorageError:
                    self.account_status.show_error()
                    return

            self.account_status.show_error()
            return

        # Save credentials when the updated account is WordPress.
        if (
            updated.destination == PublishingDestination.WORDPRESS
            and self._save_wordpress_credentials is not None
        ):
            try:
                # Preserve the existing account UUID and WordPress configuration.
                self._save_wordpress_credentials.execute(
                    Account(
                        name=updated.name.strip(),
                        destination=updated.destination,
                        id=current.id,
                        wordpress_config=(
                            updated.wordpress_config.normalized()
                            if updated.wordpress_config is not None
                            else None
                        ),
                    ),
                    password,
                )

            except CredentialStorageError:
                # Account update succeeded, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        if updated.destination == PublishingDestination.INSTAGRAM:
            instagram_account = Account(
                name=updated.name.strip(),
                destination=PublishingDestination.INSTAGRAM,
                id=current.id,
                instagram_config=updated.instagram_config,
            )

            try:
                self._save_instagram_access_token(
                    instagram_account,
                    instagram_token,
                )
            except CredentialStorageError:
                # Account update succeeded, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        # Delete obsolete credentials when converting away from WordPress.
        if (
            current.destination == PublishingDestination.WORDPRESS
            and updated.destination != PublishingDestination.WORDPRESS
            and self._delete_wordpress_credentials is not None
        ):
            try:
                self._delete_wordpress_credentials.execute(current)
            except CredentialStorageError:
                # Account update succeeded, but credential cleanup failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        if (
                current.destination == PublishingDestination.FACEBOOK
                and updated.destination != PublishingDestination.FACEBOOK
                and self._delete_facebook_credentials is not None
        ):
            try:
                self._delete_facebook_credentials.execute(current)
            except CredentialStorageError:
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        # Legacy fallback for callers without the crash-safe
        # Instagram conversion service.
        if (
                current.destination == PublishingDestination.INSTAGRAM
                and updated.destination != PublishingDestination.INSTAGRAM
                and self._update_account_with_instagram_cleanup is None
        ):
            if self._delete_instagram_credentials is None:
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

            try:
                self._delete_instagram_credentials.execute(current)
            except CredentialStorageError:
                # Account metadata was updated, but token cleanup failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_updated()
        self.accounts_changed.emit()

    def _handle_remove_account(self) -> None:
        """Remove the selected account and clean up WordPress credentials."""
        account = self.account_list.selected_account()

        if account is None:
            return

        try:
            if self._remove_account_with_credential_cleanup is not None:
                self._remove_account_with_credential_cleanup.execute(account)
            else:
                self._remove_account.execute(account)
        except AccountCredentialCleanupIncompleteError:
            # The account was removed, but credential cleanup is incomplete.
            self._refresh_accounts()
            self.account_status.show_remove_error()
            self.accounts_changed.emit()
            return
        except (AccountNotFoundError, OSError):
            # Account removal did not complete.
            self.account_status.show_remove_error()
            return

        if self._remove_account_with_credential_cleanup is not None:
            self._refresh_accounts()
            self.account_status.show_removed()
            self.accounts_changed.emit()
            return

        # Only delete credentials after successful account removal.
        if (
            account.destination == PublishingDestination.WORDPRESS
            and self._delete_wordpress_credentials is not None
        ):
            try:
                self._delete_wordpress_credentials.execute(account)
            except CredentialStorageError:
                # Account removal succeeded, but credential cleanup failed.
                self._refresh_accounts()
                self.account_status.show_remove_error()
                self.accounts_changed.emit()
                return

        if (
                account.destination == PublishingDestination.FACEBOOK
                and self._delete_facebook_credentials is not None
        ):
            try:
                self._delete_facebook_credentials.execute(account)
            except CredentialStorageError:
                self._refresh_accounts()
                self.account_status.show_remove_error()
                self.accounts_changed.emit()
                return

        if (
            account.destination == PublishingDestination.INSTAGRAM
            and self._delete_instagram_credentials is not None
        ):
            try:
                self._delete_instagram_credentials.execute(account)
            except CredentialStorageError:
                self._refresh_accounts()
                self.account_status.show_remove_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_removed()
        self.accounts_changed.emit()

    def _handle_verify_connection(self) -> None:
        """Start verification of the selected publishing account."""
        account = self.account_list.selected_account()
        if account is None:
            return

        if account.destination == PublishingDestination.WORDPRESS:
            controller = self._verification_controller
        elif account.destination == PublishingDestination.FACEBOOK:
            controller = self._facebook_verification_controller
        elif account.destination == PublishingDestination.INSTAGRAM:
            controller = self._instagram_verification_controller
        else:
            return

        if controller is None or self.verification_is_running:
            return

        self.verify_button.setEnabled(False)
        controller.start(account)

    def _load_selected_account(self) -> None:
        """Load the selected account and its saved WordPress password."""
        account = self.account_list.selected_account()

        if account is None:
            self.account_form.clear()
            return

        self.account_form.set_account(account)

        if (
                account.destination != PublishingDestination.WORDPRESS
                or self._get_wordpress_credentials is None
        ):
            return

        try:
            password = self._get_wordpress_credentials.execute(account)
        except CredentialStorageError:
            self.account_status.show_error()
            return

        if password is not None:
            self.account_form.wordpress_application_password_input.setText(
                password
            )

    def _update_account_buttons(self) -> None:
        """Synchronize account action buttons with selection."""
        account = self.account_list.selected_account()
        has_selection = account is not None

        self.update_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)

        can_verify = False

        if account is not None:
            if account.destination == PublishingDestination.WORDPRESS:
                can_verify = self._verification_controller is not None
            elif account.destination == PublishingDestination.FACEBOOK:
                can_verify = (
                        self._facebook_verification_controller is not None
                )
            elif account.destination == PublishingDestination.INSTAGRAM:
                can_verify = (
                        self._instagram_verification_controller is not None
                )

        self.verify_button.setEnabled(
            can_verify and not self.verification_is_running
        )

    def _refresh_accounts(self) -> None:
        """Refresh accounts and return to New account mode."""
        self.account_list.set_accounts(
            self._list_accounts.execute()
        )
        self._enter_new_account_mode()

    @property
    def verification_is_running(self) -> bool:
        """Report whether any connection verification is active."""
        wordpress_running = (
                self._verification_controller is not None
                and self._verification_controller.is_running
        )
        facebook_running = (
                self._facebook_verification_controller is not None
                and self._facebook_verification_controller.is_running
        )
        instagram_running = (
                self._instagram_verification_controller is not None
                and self._instagram_verification_controller.is_running
        )

        return wordpress_running or facebook_running or instagram_running

    def shutdown(self) -> None:
        """Safely finish active account background operations."""
        if self._verification_controller is not None:
            self._verification_controller.shutdown()

        if self._facebook_verification_controller is not None:
            self._facebook_verification_controller.shutdown()

        if self._instagram_verification_controller is not None:
            self._instagram_verification_controller.shutdown()

        if self._facebook_discovery_controller is not None:
            self._facebook_discovery_controller.shutdown()

    def closeEvent(self, event) -> None:
        """Finish active verification before closing the page."""
        self.shutdown()
        super().closeEvent(event)