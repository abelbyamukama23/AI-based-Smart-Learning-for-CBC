"""
apps/feed/exceptions.py
────────────────────────
Domain-specific exceptions for the feed app.
"""


class FeedError(Exception):
    """Base exception for all feed-domain errors."""


class PostNotFoundError(FeedError):
    """Raised when a Post lookup fails."""


class UnauthorizedPostActionError(FeedError):
    """Raised when a user tries to mutate a post they don't own."""
