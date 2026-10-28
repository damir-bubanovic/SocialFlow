from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QLabel,
)
from PySide6.QtCore import Qt
from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


class AccountForm(QWidget):
    """Form for entering a publishing account."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Account name")

        self.destination_input = QComboBox(self)
        self.destination_input.addItem("Select platform...", None)
        self._add_destination(PublishingDestination.FACEBOOK)
        self._add_destination(PublishingDestination.INSTAGRAM)
        self._add_destination(PublishingDestination.WORDPRESS)

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
            self._update_wordpress_fields
        )
        self._update_wordpress_fields()

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
        self.name_input.setText(account.name)

        index = self.destination_input.findData(
            account.destination
        )

        if index >= 0:
            self.destination_input.setCurrentIndex(index)

        # Clear settings from the previously selected account.
        self.wordpress_site_url_input.clear()
        self.wordpress_username_input.clear()

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
        self.name_input.clear()
        self.destination_input.setCurrentIndex(0)

        self.wordpress_site_url_input.clear()
        self.wordpress_username_input.clear()
        self.wordpress_application_password_input.clear()
        self.wordpress_application_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_visibility_button.setText("Show")
        self.password_visibility_button.setToolTip("Show password")

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
