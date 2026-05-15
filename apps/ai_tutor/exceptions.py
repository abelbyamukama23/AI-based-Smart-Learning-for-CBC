"""
apps/ai_tutor/exceptions.py
────────────────────────────
Domain-specific exceptions for the AI tutor app.
"""


class TutorError(Exception):
    """Base exception for all AI tutor domain errors."""


class ThreadNotFoundError(TutorError):
    """Raised when a ChatThread lookup fails or doesn't belong to the user."""


class AgentExecutionError(TutorError):
    """Raised when the TutorAgent loop fails unrecoverably."""


class AllProvidersFailedError(TutorError):
    """Raised when every configured LLM provider fails in the race."""
