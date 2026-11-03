
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.errors import (
    InvalidAccountError,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.views.accounts_page import AccountsPage
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import FacebookPage
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)




class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}
        self.fail_save = False
        self.fail_delete = False

    def save(self, key: str, secret: str) -> None:
        if self.fail_save:
            raise RuntimeError("Simulated credential save failure")
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        if self.fail_delete:
            raise RuntimeError("Simulated credential delete failure")
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
        save_facebook_credentials=SaveFacebookCredentials(store),
        delete_facebook_credentials=DeleteFacebookCredentials(store),
        get_facebook_credentials=GetFacebookCredentials(store),
    )
    return page, repository


def select_platform(
    page: AccountsPage,
    destination: PublishingDestination,
) -> None:
    index = page.account_form.destination_input.findData(destination)
    assert index >= 0
    page.account_form.destination_input.setCurrentIndex(index)


def select_discovered_page(
    page: AccountsPage,
    *,
    page_id: str = "123",
    page_name: str = "First Page",
    token: str = "secret-page-token",
) -> None:
    page.account_form.set_discovered_facebook_pages(
        [
            DiscoveredFacebookPage(
                page=FacebookPage(id=page_id, name=page_name),
                access_token=token,
            )
        ]
    )
    page.account_form.facebook_page_selector.setCurrentIndex(1)


def create_facebook_account(
    page: AccountsPage,
    *,
    token: str = "secret-page-token",
) -> None:
    page.account_form.name_input.setText("Facebook Account")
    select_platform(page, PublishingDestination.FACEBOOK)
    select_discovered_page(page, token=token)
    page.account_form.add_button.click()


def test_creating_facebook_account_saves_page_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    account = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(account)

    assert store.secrets[key] == "secret-page-token"
    assert "secret-page-token" not in repr(account)


def test_editing_facebook_account_replaces_page_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)
    account_id = repository.all()[0].id

    page.account_list.setCurrentRow(0)
    select_discovered_page(
        page,
        page_id="456",
        page_name="Second Page",
        token="replacement-page-token",
    )
    page.update_button.click()

    updated = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(updated)

    assert updated.id == account_id
    assert updated.facebook_config.page_id == "456"
    assert store.secrets[key] == "replacement-page-token"


def test_renaming_facebook_account_preserves_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Renamed Account")
    page.update_button.click()

    account = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(account)

    assert account.name == "Renamed Account"
    assert store.secrets[key] == "secret-page-token"


def test_manual_page_id_change_deletes_old_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")
    page.update_button.click()

    account = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(account)

    assert account.facebook_config.page_id == "999"
    assert key not in store.secrets


def test_converting_facebook_to_wordpress_deletes_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)
    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.WORDPRESS)
    page.update_button.click()

    assert repository.all()[0].destination == (
        PublishingDestination.WORDPRESS
    )
    assert key not in store.secrets


def test_removing_facebook_account_deletes_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)
    account = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(account)

    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert repository.all() == ()
    assert key not in store.secrets

def test_failed_facebook_token_save_and_account_rollback_reports_error(
    qtbot,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    store.fail_save = True

    page, repository = create_page(store)
    qtbot.addWidget(page)

    def fail_remove(_account: Account) -> None:
        raise OSError("Simulated account storage write failure")

    monkeypatch.setattr(repository, "remove", fail_remove)

    create_facebook_account(page)

    assert len(repository.all()) == 1
    assert store.secrets == {}
    assert page.account_status.property("status") == "error"


def test_failed_facebook_token_save_does_not_leave_new_account(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    page.account_form.name_input.setText("Facebook Test")
    page.account_form.destination_input.setCurrentIndex(
        page.account_form.destination_input.findData(
            PublishingDestination.FACEBOOK
        )
    )

    select_discovered_page(page)

    store.fail_save = True

    page.account_form.add_button.click()

    assert repository.all() == ()
    assert store.secrets == {}
    assert page.account_status.property("status") == "error"


def test_failed_facebook_token_save_reports_error(qtbot) -> None:
    store = FakeCredentialStore()
    store.fail_save = True

    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    assert repository.all() == ()
    assert store.secrets == {}
    assert page.account_status.property("status") == "error"


def test_failed_facebook_token_delete_reports_error(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    page.account_list.setCurrentRow(0)
    store.fail_delete = True
    page.remove_button.click()

    assert repository.all() == ()
    assert page.account_status.property("status") == "error"


def test_user_token_is_never_saved_as_page_token(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    page.account_form.name_input.setText("Facebook Account")
    select_platform(page, PublishingDestination.FACEBOOK)

    page.account_form.facebook_user_token_input.setText(
        "temporary-user-access-token"
    )

    select_discovered_page(
        page,
        token="actual-page-access-token",
    )
    page.account_form.add_button.click()

    account = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(account)

    assert store.secrets[key] == "actual-page-access-token"
    assert "temporary-user-access-token" not in store.secrets.values()


def test_discovered_page_requires_credential_save_service(qtbot) -> None:
    store = FakeCredentialStore()
    repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
    )
    qtbot.addWidget(page)

    create_facebook_account(page)

    assert repository.all() == ()
    assert store.secrets == {}
    assert page.account_status.property("status") == "error"


def test_page_id_change_without_delete_service_is_rejected(qtbot) -> None:
    store = FakeCredentialStore()
    repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_facebook_credentials=SaveFacebookCredentials(store),
        get_facebook_credentials=GetFacebookCredentials(store),
    )
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")
    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_failed_page_token_deletion_preserves_original_page(qtbot) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")

    store.fail_delete = True
    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_failed_account_update_restores_previous_facebook_token(
    qtbot,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")

    def fail_update(_current, _updated) -> None:
        raise InvalidAccountError("Simulated account update failure")

    monkeypatch.setattr(page._update_account, "execute", fail_update)

    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_page_id_change_without_credential_lookup_is_rejected(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_facebook_credentials=SaveFacebookCredentials(store),
        delete_facebook_credentials=DeleteFacebookCredentials(store),
    )
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")
    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_page_id_change_without_credential_save_is_rejected(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        get_facebook_credentials=GetFacebookCredentials(store),
        delete_facebook_credentials=DeleteFacebookCredentials(store),
    )
    qtbot.addWidget(page)

    original = Account(
        name="Facebook Account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123",
            page_name="First Page",
        ),
    )
    repository.add(original)
    store.save(
        FacebookCredentialKeys.page_access_token(original),
        "secret-page-token",
    )

    page.account_list.set_accounts(repository.all())
    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText("999")
    page.update_button.click()

    unchanged = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_failed_replacement_page_token_save_preserves_original_account(
    qtbot,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    select_discovered_page(
        page,
        page_id="456",
        page_name="Second Page",
        token="replacement-page-token",
    )

    store.fail_save = True
    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_failed_account_update_restores_original_token_after_replacement(
    qtbot,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    page.account_list.setCurrentRow(0)
    select_discovered_page(
        page,
        page_id="456",
        page_name="Second Page",
        token="replacement-page-token",
    )

    def fail_update(_current, _updated) -> None:
        raise InvalidAccountError("Simulated account update failure")

    monkeypatch.setattr(page._update_account, "execute", fail_update)

    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert store.secrets[key] == "secret-page-token"
    assert page.account_status.property("status") == "error"


def test_failed_account_update_removes_new_token_when_none_existed(
    qtbot,
    monkeypatch,
) -> None:
    store = FakeCredentialStore()
    page, repository = create_page(store)
    qtbot.addWidget(page)

    create_facebook_account(page)

    original = repository.all()[0]
    key = FacebookCredentialKeys.page_access_token(original)

    # Simulate an existing account without stored credentials.
    del store.secrets[key]

    page.account_list.setCurrentRow(0)
    select_discovered_page(
        page,
        page_id="456",
        page_name="Second Page",
        token="replacement-page-token",
    )

    def fail_update(_current, _updated) -> None:
        raise InvalidAccountError("Simulated account update failure")

    monkeypatch.setattr(page._update_account, "execute", fail_update)

    page.update_button.click()

    unchanged = repository.all()[0]

    assert unchanged.id == original.id
    assert unchanged.facebook_config.page_id == "123"
    assert key not in store.secrets
    assert page.account_status.property("status") == "error"