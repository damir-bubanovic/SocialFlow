from uuid import UUID, uuid4

from socialflow.domain.account.account_id import AccountId


def test_account_id_wraps_uuid():
    value = uuid4()

    account_id = AccountId(value)

    assert account_id.value == value


def test_account_id_string_representation():
    value = UUID("12345678-1234-5678-1234-567812345678")

    account_id = AccountId(value)

    assert str(account_id) == str(value)


def test_account_ids_with_same_uuid_are_equal():
    value = uuid4()

    first = AccountId(value)
    second = AccountId(value)

    assert first == second


def test_account_id_is_hashable():
    account_id = AccountId(uuid4())

    assert account_id in {account_id}