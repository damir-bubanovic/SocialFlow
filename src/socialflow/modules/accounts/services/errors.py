class AccountError(Exception):
    """Base exception for account operations."""

class InvalidAccountError(AccountError, ValueError):
    """Raised when an account is invalid."""

class DuplicateAccountError(AccountError):
    """Raised when an account already exists."""

class AccountNotFoundError(AccountError):
    """Raised when an account cannot be found."""

class AccountCredentialCleanupIncompleteError(AccountError):
    """Raised when account removal succeeds but cleanup remains incomplete."""