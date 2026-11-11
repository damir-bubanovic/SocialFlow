
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.delete_instagram_credentials import (
    DeleteInstagramCredentials,
)
from socialflow.modules.accounts.services.get_instagram_credentials import (
    GetInstagramCredentials,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.save_instagram_credentials import (
    SaveInstagramCredentials,
)
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
)
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import FacebookPage
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)
from socialflow.modules.accounts.services.update_account_with_instagram_cleanup import (
    UpdateAccountWithInstagramCleanup,
)
from socialflow.modules.accounts.views.accounts_page import AccountsPage


class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}
        self.fail_save = False

    def save(self, key: str, secret: str) -> None:
        if self.fail_save:
            raise RuntimeError("Simulated secure storage failure")
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        self.secrets.pop(key, None)


def create_page(
    store: FakeCredentialStore,
) -> tuple[AccountsPage, InMemoryAccountRepository]:
    repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_instagram_credentials=SaveInstagramCredentials(store),
        get_instagram_credentials=GetInstagramCredentials(store),
        delete_instagram_credentials=DeleteInstagramCredentials(store),
    )
    return page, repository


def create_page_with_conversion_cleanup(
    store: FakeCredentialStore,
    tmp_path,
) -> tuple[
    AccountsPage,
    InMemoryAccountRepository,
    JsonPendingCredentialCleanupRepository,
]:
    repository = InMemoryAccountRepository()
    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json",
    )
    update_account = UpdateAccount(repository)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=update_account,
        save_instagram_credentials=SaveInstagramCredentials(store),
        get_instagram_credentials=GetInstagramCredentials(store),
        delete_instagram_credentials=DeleteInstagramCredentials(store),
        save_facebook_credentials=SaveFacebookCredentials(store),
        get_facebook_credentials=GetFacebookCredentials(store),
        delete_facebook_credentials=DeleteFacebookCredentials(store),
        update_account_with_instagram_cleanup=(
            UpdateAccountWithInstagramCleanup(
                update_account=update_account,
                cleanup_repository=journal,
                credential_store=store,
                account_repository=repository,
            )
        ),
    )
    return page, repository, journal

def select_platform(
    page: AccountsPage,
    destination: PublishingDestination,
) -> None:
    index = page.account_form.destination_input.findData(destination)
    assert index >= 0
    page.account_form.destination_input.setCurrentIndex(index)


def create_instagram_account(
    page: AccountsPage,
    *,
    token: str = "original-secret-token",
) -> None:
    select_platform(page, PublishingDestination.INSTAGRAM)
    page.account_form.name_input.setText("Instagram Account")
    page.account_form.instagram_user_id_input.setText("12345")
    page.account_form.instagram_username_input.setText("example_user")
    page.account_form.instagram_access_token_input.setText(token)
    page.account_form.add_button.click()


def test_create_instagram_account_saves_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    account = repository.all()[0]
    key = InstagramCredentialKeys.access_token(account)

    assert store.secrets[key] == "original-secret-token"
    assert account.instagram_config.instagram_user_id == "12345"
    assert "original-secret-token" not in repr(account)
    assert page.account_status.property("status") == "success"


def test_create_instagram_account_normalizes_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page, token="  secret-token  ")

    account = repository.all()[0]
    key = InstagramCredentialKeys.access_token(account)

    assert store.secrets[key] == "secret-token"


def test_create_instagram_account_without_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page, token="")

    assert len(repository.all()) == 1
    assert store.secrets == {}
    assert page.account_status.property("status") == "success"


def test_create_instagram_account_reports_save_failure(qtbot) -> None:
    store = FakeCredentialStore()
    store.fail_save = True

    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    # Current behavior: the account remains after a credential failure.
    assert len(repository.all()) == 1
    assert store.secrets == {}
    assert page.account_status.property("status") == "error"


def test_edit_instagram_account_replaces_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)
    original = repository.all()[0]

    page.account_list.setCurrentRow(0)
    page.account_form.instagram_access_token_input.setText(
        "replacement-secret-token"
    )
    page.update_button.click()

    updated = repository.all()[0]
    key = InstagramCredentialKeys.access_token(updated)

    assert updated.id == original.id
    assert store.secrets[key] == "replacement-secret-token"
    assert page.account_status.property("status") == "success"


def test_edit_instagram_account_with_blank_token_preserves_existing(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Renamed Instagram")
    page.update_button.click()

    updated = repository.all()[0]
    key = InstagramCredentialKeys.access_token(updated)

    assert updated.name == "Renamed Instagram"
    assert store.secrets[key] == "original-secret-token"


def test_edit_instagram_user_id_preserves_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.instagram_user_id_input.setText("67890")
    page.update_button.click()

    updated = repository.all()[0]
    key = InstagramCredentialKeys.access_token(updated)

    assert updated.instagram_config.instagram_user_id == "67890"
    assert store.secrets[key] == "original-secret-token"


def test_edit_instagram_account_reports_save_failure(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Updated Instagram")
    page.account_form.instagram_access_token_input.setText(
        "replacement-secret-token"
    )

    store.fail_save = True
    page.update_button.click()

    updated = repository.all()[0]
    key = InstagramCredentialKeys.access_token(updated)

    # Current behavior: account metadata is updated before token saving.
    assert updated.name == "Updated Instagram"
    assert store.secrets[key] == "original-secret-token"
    assert page.account_status.property("status") == "error"


def test_create_clears_token_from_form(qtbot) -> None:
    store = FakeCredentialStore()
    page, _repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    assert page.account_form.instagram_access_token() == ""


def test_update_clears_token_from_form(qtbot) -> None:
    store = FakeCredentialStore()
    page, _repository = create_page(store)
    qtbot.addWidget(page)

    create_instagram_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.instagram_access_token_input.setText(
        "replacement-secret-token"
    )
    page.update_button.click()

    assert page.account_form.instagram_access_token() == ""


def test_switching_to_facebook_does_not_save_instagram_token(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    select_platform(page, PublishingDestination.INSTAGRAM)
    page.account_form.instagram_access_token_input.setText(
        "should-not-be-saved"
    )
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Facebook Account")
    page.account_form.add_button.click()

    assert repository.all()[0].destination == (
        PublishingDestination.FACEBOOK
    )
    assert store.secrets == {}


def test_gui_conversion_deletes_instagram_token_and_clears_journal(
    qtbot,
    tmp_path,
) -> None:
    store = FakeCredentialStore()
    page, repository, journal = create_page_with_conversion_cleanup(
        store,
        tmp_path,
    )
    qtbot.addWidget(page)

    create_instagram_account(page)
    original = repository.all()[0]
    key = InstagramCredentialKeys.access_token(original)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Converted Facebook Account")
    page.update_button.click()

    converted = repository.all()[0]

    assert converted.id == original.id
    assert converted.destination == PublishingDestination.FACEBOOK
    assert key not in store.secrets
    assert journal.all() == ()
    assert page.account_status.property("status") == "success"


def test_gui_conversion_retains_journal_when_token_deletion_fails(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository, journal = create_page_with_conversion_cleanup(
        store,
        tmp_path,
    )
    qtbot.addWidget(page)

    create_instagram_account(page)
    original = repository.all()[0]
    key = InstagramCredentialKeys.access_token(original)

    def fail_delete(_key: str) -> None:
        raise OSError("Simulated credential deletion failure")

    monkeypatch.setattr(store, "delete", fail_delete)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Converted Facebook Account")
    page.update_button.click()

    assert repository.all()[0].destination == PublishingDestination.FACEBOOK
    assert store.secrets[key] == "original-secret-token"
    assert journal.all() == (key,)
    assert page.account_status.property("status") == "error"


def test_gui_conversion_preserves_instagram_token_when_update_fails(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository, journal = create_page_with_conversion_cleanup(
        store,
        tmp_path,
    )
    qtbot.addWidget(page)

    create_instagram_account(page)
    original = repository.all()[0]
    key = InstagramCredentialKeys.access_token(original)

    from socialflow.modules.accounts.services.errors import (
        InvalidAccountError,
    )

    def fail_update(_current, _updated) -> None:
        raise InvalidAccountError("Simulated account update failure")

    monkeypatch.setattr(repository, "update", fail_update)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Converted Facebook Account")
    page.update_button.click()

    # The failed conversion leaves the Instagram account unchanged.
    assert repository.all() == (original,)

    # Its original credential remains available.
    assert store.secrets[key] == "original-secret-token"

    # The service verified that conversion did not occur, so no
    # pending credential cleanup is necessary.
    assert journal.all() == ()

    assert page.account_status.property("status") == "error"

def test_gui_conversion_rolls_back_facebook_token_when_journal_write_fails(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository, journal = create_page_with_conversion_cleanup(
        store,
        tmp_path,
    )
    qtbot.addWidget(page)

    create_instagram_account(page)

    original = repository.all()[0]
    instagram_key = InstagramCredentialKeys.access_token(original)
    facebook_key = f"facebook:{original.id}:page_access_token"

    def fail_journal_add(_key: str) -> None:
        raise OSError("Simulated cleanup journal write failure")

    monkeypatch.setattr(journal, "add", fail_journal_add)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Converted Facebook Account")

    page.account_form.set_discovered_facebook_pages(
        [
            DiscoveredFacebookPage(
                page=FacebookPage(
                    id="123",
                    name="Selected Facebook Page",
                ),
                access_token="replacement-facebook-token",
            )
        ]
    )
    page.account_form.facebook_page_selector.setCurrentIndex(1)

    page.update_button.click()

    # The failed journal write must prevent account conversion.
    assert repository.all() == (original,)

    # The original Instagram token must remain available.
    assert store.secrets[instagram_key] == "original-secret-token"

    # The newly saved Facebook token must be rolled back.
    assert facebook_key not in store.secrets

    # No cleanup intent was successfully persisted.
    assert journal.all() == ()

    # The GUI must report the failed operation.
    assert page.account_status.property("status") == "error"

def test_gui_conversion_preserves_facebook_token_when_update_persists_then_fails(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository, journal = create_page_with_conversion_cleanup(
        store,
        tmp_path,
    )
    qtbot.addWidget(page)

    create_instagram_account(page)

    original = repository.all()[0]
    instagram_key = InstagramCredentialKeys.access_token(original)
    facebook_key = f"facebook:{original.id}:page_access_token"

    # Allow the real update to persist metadata before simulating
    # a failure reported to the conversion coordinator.
    update_service = page._update_account
    original_execute = update_service.execute

    def persist_then_fail(current, updated) -> None:
        original_execute(current, updated)
        raise OSError("Simulated failure after account persistence")

    monkeypatch.setattr(
        update_service,
        "execute",
        persist_then_fail,
    )

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.name_input.setText("Converted Facebook Account")

    page.account_form.set_discovered_facebook_pages(
        [
            DiscoveredFacebookPage(
                page=FacebookPage(
                    id="123",
                    name="Selected Facebook Page",
                ),
                access_token="replacement-facebook-token",
            )
        ]
    )
    page.account_form.facebook_page_selector.setCurrentIndex(1)

    page.update_button.click()

    # Metadata was persisted before the simulated failure.
    persisted = repository.all()[0]
    assert persisted.id == original.id
    assert persisted.destination == PublishingDestination.FACEBOOK
    assert persisted.facebook_config.page_id == "123"

    # The replacement Facebook token belongs to the persisted account.
    assert store.secrets[facebook_key] == "replacement-facebook-token"

    # Instagram cleanup was interrupted, so its original token
    # and pending cleanup intent must remain for startup recovery.
    assert store.secrets[instagram_key] == "original-secret-token"
    assert journal.all() == (instagram_key,)

    # The GUI reports the failure rather than claiming success.
    assert page.account_status.property("status") == "error"