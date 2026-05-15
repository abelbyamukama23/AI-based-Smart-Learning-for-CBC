"""
apps/curriculum/exceptions.py
──────────────────────────────
Domain-specific exceptions for the curriculum app.

Circuit Breaker principle: callers get typed exceptions, not silent empty lists.
"""


class CurriculumError(Exception):
    """Base exception for all curriculum-domain errors."""


class RAGServiceError(CurriculumError):
    """
    Raised when the ChromaDB vector store is unavailable or returns an
    unrecoverable error.  Callers should catch this and fall back gracefully
    rather than letting a bare Exception bubble up silently.
    """


class EmbeddingError(CurriculumError):
    """Raised when the Gemini embedding API call fails."""


class LessonNotFoundError(CurriculumError):
    """Raised when a Lesson lookup by ID finds no row."""
