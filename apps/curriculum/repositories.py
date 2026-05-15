"""
apps/curriculum/repositories.py
────────────────────────────────
Repository Pattern for the curriculum domain.

Design Principles:
  • All ORM queries are centralised here — no raw `.objects.filter()` in views.
  • Callers receive domain objects or typed exceptions — never raw QuerySets
    from untested view code.
  • Adding a new filter or eager-load requires changing one method, not
    hunting every view that touches Lesson.
"""

from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from .constants import CURRICULUM_SEARCH_LIMIT, COMPETENCY_LIST_LIMIT
from .exceptions import LessonNotFoundError
from .models import CurriculumFile, Lesson, Subject, Level, Competency


class LessonRepository:
    """All ORM operations for the Lesson model."""

    @staticmethod
    def get_by_id(lesson_id) -> Lesson:
        """
        Fetch a single lesson with all related data eagerly loaded.
        Raises LessonNotFoundError when no row matches.
        """
        try:
            return (
                Lesson.objects
                .select_related("subject", "class_level")
                .prefetch_related("competencies")
                .get(pk=lesson_id)
            )
        except Lesson.DoesNotExist:
            raise LessonNotFoundError(f"Lesson {lesson_id} not found.")

    @staticmethod
    def list_all() -> QuerySet:
        """Base queryset for lesson lists — always eager-loads FK relations."""
        return Lesson.objects.select_related("subject", "class_level").all()

    @staticmethod
    def search(subject: str = "", class_level: str = "", query: str = "") -> QuerySet:
        """
        Filtered lesson search used by both the MCP tool and the API.
        Returns a QuerySet capped at CURRICULUM_SEARCH_LIMIT.
        """
        qs = Lesson.objects.select_related("subject", "class_level").filter(
            subject__is_active=True
        )
        if subject:
            qs = qs.filter(subject__subject_name__icontains=subject)
        if class_level:
            qs = qs.filter(class_level__level_name__iexact=class_level)
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        return qs[:CURRICULUM_SEARCH_LIMIT]


class SubjectRepository:
    """All ORM operations for the Subject model."""

    @staticmethod
    def list_active() -> QuerySet:
        return (
            Subject.objects
            .filter(is_active=True)
            .annotate(competency_count=Count("competencies"))
        )

    @staticmethod
    def list_active_values():
        """Lightweight values-only query for the MCP tool (no model hydration)."""
        return Subject.objects.filter(is_active=True).values("id", "subject_name")


class CompetencyRepository:
    """All ORM operations for the Competency model."""

    @staticmethod
    def list_for_subject_and_level(subject: str, class_level: str) -> QuerySet:
        return (
            Competency.objects
            .select_related("subject", "level")
            .filter(
                subject__subject_name__icontains=subject,
                level__level_name__iexact=class_level,
            )[:COMPETENCY_LIST_LIMIT]
        )


class LibraryRepository:
    """All ORM operations for the CurriculumFile model."""

    @staticmethod
    def base_queryset() -> QuerySet:
        return CurriculumFile.objects.select_related("subject", "class_level").all()

    @staticmethod
    def search_lessons_by_title(query: str, limit: int = 3) -> QuerySet:
        """
        Keyword RAG fallback — searches Lesson rows by title.

        Returns Lesson instances (which have body_html, description, etc.) so
        callers can safely access all Lesson fields without AttributeError.
        This is the correct model for the MCP tool's keyword fallback path.
        """
        return (
            Lesson.objects
            .filter(title__icontains=query)
            .select_related("subject", "class_level")[:limit]
        )

    @staticmethod
    def search_files_by_title(query: str, limit: int = 3) -> QuerySet:
        """
        Keyword search against CurriculumFile rows (textbooks, PDFs, maps).
        Use when you want library assets specifically — not lesson content.
        """
        return (
            CurriculumFile.objects
            .filter(title__icontains=query)
            .select_related("subject", "class_level")[:limit]
        )

