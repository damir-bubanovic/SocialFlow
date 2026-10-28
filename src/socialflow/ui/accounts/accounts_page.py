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

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.application.accounts.update_account import UpdateAccount
from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.application.credentials.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)
from socialflow.application.credentials.get_wordpress_credentials import (
    GetWordPressCredentials,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)
from socialflow.application.credentials.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.accounts.account_form import AccountForm
from socialflow.ui.accounts.account_list import AccountList
from socialflow.ui.accounts.account_status import AccountStatus
from socialflow.ui.accounts.wordpress_verification_controller import (
    WordPressVerificationController,
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
    ) -> None:
        super().__init__(parent)

        self._add_account = add_account
        self._list_accounts = list_accounts
        self._remove_account = remove_account
        self._update_account = update_account
        self._wordpress_connection_verifier = wordpress_connection_verifier
        self._save_wordpress_credentials = save_wordpress_credentials
        self._delete_wordpress_credentials = delete_wordpress_credentials
        self._get_wordpress_credentials = get_wordpress_credentials
        self._verification_controller = (
            WordPressVerificationController(
                wordpress_connection_verifier,
                parent=self,
            )
            if wordpress_connection_verifier is not None
            else None
        )

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

        self._refresh_accounts()

    def _enter_new_account_mode(self) -> None:
        """Show a blank form for creating an account."""
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

    def _handle_add_account(self) -> None:
        """Add an account and then save its WordPress credentials."""
        if self.account_form.selected_destination() is None:
            self.account_status.show_error()
            return

        account = self.account_form.account()
        password = self.account_form.wordpress_application_password()

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

        try:
            self._update_account.execute(
                current,
                updated,
            )
        except (
            AccountNotFoundError,
            DuplicateAccountError,
            InvalidAccountError,
        ):
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

        self._refresh_accounts()
        self.account_status.show_updated()
        self.accounts_changed.emit()

    def _handle_remove_account(self) -> None:
        """Remove the selected account and clean up WordPress credentials."""
        account = self.account_list.selected_account()

        if account is None:
            return

        try:
            self._remove_account.execute(account)
        except AccountNotFoundError:
            self.account_status.show_remove_error()
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

        self._refresh_accounts()
        self.account_status.show_removed()
        self.accounts_changed.emit()

    def _handle_verify_connection(self) -> None:
        """Start verification of the selected WordPress account."""
        account = self.account_list.selected_account()
        controller = self._verification_controller

        if (
            account is None
            or account.destination != PublishingDestination.WORDPRESS
            or controller is None
            or controller.is_running
        ):
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

        self.verify_button.setEnabled(
            account is not None
            and account.destination == PublishingDestination.WORDPRESS
            and self._verification_controller is not None
            and not self._verification_controller.is_running
        )

    def _refresh_accounts(self) -> None:
        """Refresh accounts and return to New account mode."""
        self.account_list.set_accounts(
            self._list_accounts.execute()
        )
        self._enter_new_account_mode()

    @property
    def verification_is_running(self) -> bool:
        """Report whether WordPress verification is still active."""
        return (
                self._verification_controller is not None
                and self._verification_controller.is_running
        )

    def shutdown(self) -> None:
        """Safely finish any active WordPress verification."""
        if self._verification_controller is not None:
            self._verification_controller.shutdown()

    def closeEvent(self, event) -> None:
        """Finish active verification before closing the page."""
        self.shutdown()
        super().closeEvent(event)