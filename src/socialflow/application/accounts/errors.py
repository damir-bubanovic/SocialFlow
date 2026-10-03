class AccountError(Exception):
    """Base exception for account operations."""


class InvalidAccountError(AccountError, ValueError):
    """Raised when an account is invalid."""

class DuplicateAccountError(AccountError):
    """Raised when an account already exists."""