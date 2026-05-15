"""
apps/accounts/exceptions.py
────────────────────────────
Domain-specific exceptions for the accounts app.
Following the principle: never let infrastructure errors bleed into domain logic.
"""


class AccountsError(Exception):
    """Base exception for all accounts-domain errors."""


class DuplicateEmailError(AccountsError):
    """Raised when registration is attempted with an already-registered email."""


class InvalidRoleDataError(AccountsError):
    """Raised when required role-specific fields are missing (e.g. Learner without school)."""


class UserNotFoundError(AccountsError):
    """Raised when a User lookup fails."""
