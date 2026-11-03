from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QLabel,
)
from PySide6.QtCore import Qt, Signal
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.core.destination import (
    PublishingDestination,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)



class AccountForm(QWidget):
    """Form for entering a publishing account."""
    facebook_discovery_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Account name")

        self.destination_input = QComboBox(self)
        self.destination_input.addItem("Select platform...", None)
        self._add_destination(PublishingDestination.FACEBOOK)
        self._add_destination(PublishingDestination.INSTAGRAM)
        self._add_destination(PublishingDestination.WORDPRESS)

        self.facebook_page_id_input = QLineEdit(self)
        self.facebook_page_id_input.setPlaceholderText(
            "Facebook Page ID"
        )

        self.facebook_page_name_input = QLineEdit(self)
        self.facebook_page_name_input.setPlaceholderText(
            "Facebook Page name"
        )
        self.facebook_user_token_input = QLineEdit(self)
        self.facebook_user_token_input.setPlaceholderText(
            "Temporary Facebook user access token"
        )
        self.facebook_user_token_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.facebook_discover_button = QPushButton(
            "Discover Pages", self
        )
        self.facebook_discover_button.clicked.connect(
            self._request_facebook_discovery
        )

        self.facebook_page_selector = QComboBox(self)
        self.facebook_page_selector.addItem(
            "Select discovered Page...", None
        )
        self.facebook_page_selector.setEnabled(False)
        self.facebook_page_selector.currentIndexChanged.connect(
            self._select_discovered_facebook_page
        )

        self._discovered_facebook_pages: list[
            DiscoveredFacebookPage
        ] = []
        self._selected_facebook_page_token = ""
        self._selected_facebook_page_id = ""

        self.facebook_page_id_input.textChanged.connect(
            self._invalidate_facebook_page_token
        )

        self.wordpress_site_url_input = QLineEdit(self)
        self.wordpress_site_url_input.setPlaceholderText(
            "https://example.com"
        )

        self.wordpress_username_input = QLineEdit(self)
        self.wordpress_username_input.setPlaceholderText(
            "WordPress username"
        )

        self.wordpress_application_password_input = QLineEdit(self)
        self.wordpress_application_password_input.setPlaceholderText(
            "WordPress application password"
        )
        self.wordpress_application_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_visibility_button = QPushButton("Show", self)
        self.password_visibility_button.setToolTip("Show password")
        self.password_visibility_button.setFixedWidth(65)
        self.password_visibility_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.password_visibility_button.clicked.connect(
            self._toggle_password_visibility
        )

        self.wordpress_password_layout = QHBoxLayout()
        self.wordpress_password_layout.setContentsMargins(0, 0, 0, 0)
        self.wordpress_password_layout.setSpacing(6)

        self.wordpress_password_layout.addWidget(
            self.wordpress_application_password_input
        )
        self.wordpress_password_layout.addWidget(
            self.password_visibility_button
        )

        self.add_button = QPushButton("Create account", self)

        layout = QFormLayout()
        layout.addRow("Name", self.name_input)
        layout.addRow("Platform", self.destination_input)

        self.facebook_page_id_label = QLabel("Page ID", self)
        self.facebook_page_name_label = QLabel("Page name", self)
        self.facebook_user_token_label = QLabel(
            "User access token", self
        )
        self.facebook_page_selector_label = QLabel(
            "Discovered Pages", self
        )

        layout.addRow(
            self.facebook_user_token_label,
            self.facebook_user_token_input,
        )
        layout.addRow(self.facebook_discover_button)
        layout.addRow(
            self.facebook_page_selector_label,
            self.facebook_page_selector,
        )

        layout.addRow(
            self.facebook_page_id_label,
            self.facebook_page_id_input,
        )
        layout.addRow(
            self.facebook_page_name_label,
            self.facebook_page_name_input,
        )

        self.wordpress_site_url_label = QLabel("Site URL", self)
        self.wordpress_username_label = QLabel("Username", self)
        self.wordpress_password_label = QLabel(
            "Application password", self
        )

        layout.addRow(
            self.wordpress_site_url_label,
            self.wordpress_site_url_input,
        )
        layout.addRow(
            self.wordpress_username_label,
            self.wordpress_username_input,
        )
        layout.addRow(
            self.wordpress_password_label,
            self.wordpress_password_layout,
        )
        layout.addRow(self.add_button)

        self.setLayout(layout)

        self.destination_input.currentIndexChanged.connect(
            self._update_platform_fields
        )
        self._update_platform_fields()

    def _toggle_password_visibility(self) -> None:
        """Toggle the WordPress password between masked and visible."""
        password_input = self.wordpress_application_password_input

        if password_input.echoMode() == QLineEdit.EchoMode.Password:
            password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_visibility_button.setText("Hide")
            self.password_visibility_button.setToolTip("Hide password")
        else:
            password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_visibility_button.setText("Show")
            self.password_visibility_button.setToolTip("Show password")

    def account(self) -> Account:
        """Return the account represented by the form."""
        destination = self.selected_destination()

        return Account(
            name=self.name_input.text(),
            destination=destination,
            wordpress_config=(
                self.wordpress_connection_config()
                if destination == PublishingDestination.WORDPRESS
                else None
            ),
            facebook_config=(
                self.facebook_page_config()
                if destination == PublishingDestination.FACEBOOK
                else None
            ),
        )

    def selected_destination(self) -> PublishingDestination | None:
        """Return the selected platform, or None if not selected."""
        value = self.destination_input.currentData()

        if value is None:
            return None

        return PublishingDestination(value)

    def _add_destination(
        self,
        destination: PublishingDestination,
    ) -> None:
        """Add a publishing destination to the selector."""
        self.destination_input.addItem(
            destination.display_name,
            destination,
        )

    def set_account(self, account: Account) -> None:
        """Populate the form with an existing account."""
        self.clear_discovered_facebook_pages()
        self.facebook_user_token_input.clear()
        self.set_facebook_discovery_running(False)

        self.name_input.setText(account.name)

        index = self.destination_input.findData(
            account.destination
        )

        if index >= 0:
            self.destination_input.setCurrentIndex(index)

        # Clear settings from the previously selected account.
        self.wordpress_site_url_input.clear()
        self.wordpress_username_input.clear()
        self.facebook_page_id_input.clear()
        self.facebook_page_name_input.clear()

        if (
                account.destination == PublishingDestination.FACEBOOK
                and account.facebook_config is not None
        ):
            self.facebook_page_id_input.setText(
                account.facebook_config.page_id
            )
            self.facebook_page_name_input.setText(
                account.facebook_config.page_name
            )

        # Restore saved WordPress connection settings.
        if (
                account.destination == PublishingDestination.WORDPRESS
                and account.wordpress_config is not None
        ):
            self.wordpress_site_url_input.setText(
                account.wordpress_config.site_url
            )
            self.wordpress_username_input.setText(
                account.wordpress_config.username
            )

        # Never retain a password when switching accounts.
        self.wordpress_application_password_input.clear()
        self.wordpress_application_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_visibility_button.setText("Show")
        self.password_visibility_button.setToolTip("Show password")

    def clear(self) -> None:
        """Reset the account form."""
        self.clear_discovered_facebook_pages()
        self.facebook_user_token_input.clear()
        self.set_facebook_discovery_running(False)

        self.name_input.clear()
        self.destination_input.setCurrentIndex(0)

        self.wordpress_site_url_input.clear()
        self.wordpress_username_input.clear()
        self.facebook_page_id_input.clear()
        self.facebook_page_name_input.clear()
        self.wordpress_application_password_input.clear()
        self.wordpress_application_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_visibility_button.setText("Show")
        self.password_visibility_button.setToolTip("Show password")

    def _update_platform_fields(self) -> None:
        """Show fields for the selected publishing platform."""
        is_facebook = (
                self.selected_destination()
                == PublishingDestination.FACEBOOK
        )

        if not is_facebook:
            self.facebook_user_token_input.clear()
            self.clear_discovered_facebook_pages()

        for widget in (
                self.facebook_user_token_label,
                self.facebook_user_token_input,
                self.facebook_discover_button,
                self.facebook_page_selector_label,
                self.facebook_page_selector,
                self.facebook_page_id_label,
                self.facebook_page_id_input,
                self.facebook_page_name_label,
                self.facebook_page_name_input,
        ):
            widget.setVisible(is_facebook)

        self._update_wordpress_fields()

    def _update_wordpress_fields(self) -> None:
        """Show WordPress-specific fields only for WordPress accounts."""
        is_wordpress = (
                self.selected_destination()
                == PublishingDestination.WORDPRESS
        )

        for widget in (
                self.wordpress_site_url_label,
                self.wordpress_site_url_input,
                self.wordpress_username_label,
                self.wordpress_username_input,
                self.wordpress_password_label,
                self.wordpress_application_password_input,
                self.password_visibility_button,
        ):
            widget.setVisible(is_wordpress)

    def wordpress_connection_config(
        self,
    ) -> WordPressConnectionConfig:
        """Return normalized WordPress connection settings."""
        return WordPressConnectionConfig(
            site_url=self.wordpress_site_url_input.text(),
            username=self.wordpress_username_input.text(),
        ).normalized()

    def wordpress_application_password(self) -> str:
        """Return the application password entered by the user."""
        return self.wordpress_application_password_input.text()


    def _request_facebook_discovery(self) -> None:
        """Request Page discovery using the temporary user token."""
        token = self.facebook_user_token_input.text().strip()
        self.facebook_user_token_input.clear()

        if not token:
            return

        self.clear_discovered_facebook_pages()
        self.facebook_discover_button.setEnabled(False)
        self.facebook_discovery_requested.emit(token)

    def set_facebook_discovery_running(self, running: bool) -> None:
        """Update the discovery button state."""
        self.facebook_discover_button.setEnabled(not running)

    def set_discovered_facebook_pages(
        self,
        pages: list[DiscoveredFacebookPage],
    ) -> None:
        """Populate the discovered Facebook Pages dropdown."""
        self.clear_discovered_facebook_pages()

        self._discovered_facebook_pages = list(pages)

        for discovered in pages:
            self.facebook_page_selector.addItem(
                discovered.page.name,
                discovered.page.id,
            )

        self.facebook_page_selector.setEnabled(bool(pages))

    def _select_discovered_facebook_page(self, index: int) -> None:
        """Populate Page settings from the selected discovery result."""
        if index <= 0:
            self._selected_facebook_page_token = ""
            return

        page_index = index - 1
        if page_index >= len(self._discovered_facebook_pages):
            return

        discovered = self._discovered_facebook_pages[page_index]

        self._selected_facebook_page_id = discovered.page.id

        self.facebook_page_id_input.setText(discovered.page.id)
        self.facebook_page_name_input.setText(discovered.page.name)
        self._selected_facebook_page_token = discovered.access_token

    def _invalidate_facebook_page_token(self, page_id: str) -> None:
        """Discard the token if the Page ID no longer matches."""
        if page_id.strip() != self._selected_facebook_page_id:
            self._selected_facebook_page_token = ""

    def selected_facebook_page_token(self) -> str:
        """Return the selected Page token for secure storage."""
        return self._selected_facebook_page_token

    def clear_discovered_facebook_pages(self) -> None:
        """Discard discovered Pages and their temporary tokens."""
        self._selected_facebook_page_token = ""
        self._selected_facebook_page_id = ""
        self._discovered_facebook_pages.clear()

        self.facebook_page_selector.blockSignals(True)
        self.facebook_page_selector.clear()
        self.facebook_page_selector.addItem(
            "Select discovered Page...", None
        )
        self.facebook_page_selector.blockSignals(False)

        self.facebook_page_selector.setEnabled(False)


    def facebook_page_config(self) -> FacebookPageConfig:
        """Return normalized, non-secret Facebook Page settings."""
        return FacebookPageConfig(
            page_id=self.facebook_page_id_input.text(),
            page_name=self.facebook_page_name_input.text(),
        ).normalized()