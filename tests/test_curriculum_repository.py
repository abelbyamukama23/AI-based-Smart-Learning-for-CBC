"""
tests/test_curriculum_repository.py
──────────────────────────────────────
Unit & integration tests for the curriculum Repository layer.

Run:
    pytest tests/test_curriculum_repository.py -v
"""

from __future__ import annotations

import pytest

from apps.curriculum.constants import CURRICULUM_SEARCH_LIMIT
from apps.curriculum.exceptions import LessonNotFoundError


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def subject(db):
    from apps.curriculum.models import Subject
    return Subject.objects.create(subject_name="Biology", is_active=True)


@pytest.fixture
def inactive_subject(db):
    from apps.curriculum.models import Subject
    return Subject.objects.create(subject_name="OldSubject", is_active=False)


@pytest.fixture
def level(db):
    from apps.curriculum.models import Level
    return Level.objects.create(level_name="S1", sort_order=1)


@pytest.fixture
def lesson(db, subject, level):
    from apps.curriculum.models import Lesson, ContentType
    return Lesson.objects.create(
        title="Photosynthesis",
        description="How plants make food",
        subject=subject,
        class_level=level,
        content_type=ContentType.LESSON,
        body_html="<p>Chloroplasts absorb sunlight...</p>",
    )


@pytest.fixture
def library_file(db, subject, level):
    from apps.curriculum.models import CurriculumFile, FileType
    return CurriculumFile.objects.create(
        title="Biology Textbook S1",
        description="Official NCDC Biology book",
        file_type=FileType.PDF,
        file="library/bio_s1.pdf",
        subject=subject,
        class_level=level,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LessonRepository
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestLessonRepository:

    def test_get_by_id_returns_lesson(self, lesson):
        from apps.curriculum.repositories import LessonRepository
        found = LessonRepository.get_by_id(lesson.pk)
        assert found.pk == lesson.pk
        assert found.title == "Photosynthesis"

    def test_get_by_id_raises_lesson_not_found(self, db):
        from apps.curriculum.repositories import LessonRepository
        import uuid
        with pytest.raises(LessonNotFoundError):
            LessonRepository.get_by_id(uuid.uuid4())

    def test_list_all_returns_queryset(self, lesson):
        from apps.curriculum.repositories import LessonRepository
        qs = LessonRepository.list_all()
        assert lesson in qs

    def test_search_filters_by_subject(self, lesson, subject, db):
        from apps.curriculum.repositories import LessonRepository
        results = LessonRepository.search(subject="Biology")
        assert lesson in results

    def test_search_filters_by_class_level(self, lesson, db):
        from apps.curriculum.repositories import LessonRepository
        results = LessonRepository.search(class_level="S1")
        assert lesson in results

    def test_search_by_query_text(self, lesson, db):
        from apps.curriculum.repositories import LessonRepository
        results = LessonRepository.search(query="Photosynthesis")
        assert lesson in results

    def test_search_excludes_inactive_subjects(self, inactive_subject, level, db):
        from apps.curriculum.models import Lesson, ContentType
        from apps.curriculum.repositories import LessonRepository
        dead_lesson = Lesson.objects.create(
            title="Dead lesson",
            description="From inactive subject",
            subject=inactive_subject,
            class_level=level,
            content_type=ContentType.LESSON,
        )
        results = LessonRepository.search()
        assert dead_lesson not in results

    def test_search_respects_curriculum_search_limit(self, subject, level, db):
        from apps.curriculum.models import Lesson, ContentType
        from apps.curriculum.repositories import LessonRepository
        # Create more than CURRICULUM_SEARCH_LIMIT lessons
        for i in range(CURRICULUM_SEARCH_LIMIT + 5):
            Lesson.objects.create(
                title=f"Lesson {i}",
                description="Filler",
                subject=subject,
                class_level=level,
                content_type=ContentType.LESSON,
            )
        results = LessonRepository.search()
        assert len(results) <= CURRICULUM_SEARCH_LIMIT


# ═══════════════════════════════════════════════════════════════════════════════
# SubjectRepository
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestSubjectRepository:

    def test_list_active_excludes_inactive(self, subject, inactive_subject):
        from apps.curriculum.repositories import SubjectRepository
        active = list(SubjectRepository.list_active())
        names = [s.subject_name for s in active]
        assert "Biology" in names
        assert "OldSubject" not in names

    def test_list_active_values_returns_id_and_name(self, subject):
        from apps.curriculum.repositories import SubjectRepository
        values = list(SubjectRepository.list_active_values())
        assert any(v["subject_name"] == "Biology" for v in values)
        assert all("id" in v and "subject_name" in v for v in values)


# ═══════════════════════════════════════════════════════════════════════════════
# LibraryRepository
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestLibraryRepository:

    def test_base_queryset_returns_curriculum_files(self, library_file):
        from apps.curriculum.repositories import LibraryRepository
        qs = LibraryRepository.base_queryset()
        assert library_file in qs

    def test_search_lessons_by_title_returns_lesson_instances(self, lesson):
        """search_lessons_by_title must return Lesson objects (which have body_html)."""
        from apps.curriculum.models import Lesson
        from apps.curriculum.repositories import LibraryRepository
        results = LibraryRepository.search_lessons_by_title("Photosynthesis")
        assert all(isinstance(r, Lesson) for r in results)
        assert lesson in results

    def test_search_lessons_by_title_has_body_html(self, lesson):
        """Each result has the body_html attribute — no AttributeError possible."""
        from apps.curriculum.repositories import LibraryRepository
        results = LibraryRepository.search_lessons_by_title("Photosynthesis")
        for r in results:
            assert hasattr(r, "body_html"), "body_html missing — wrong model returned"

    def test_search_files_by_title_returns_curriculum_file_instances(self, library_file):
        """search_files_by_title must return CurriculumFile objects."""
        from apps.curriculum.models import CurriculumFile
        from apps.curriculum.repositories import LibraryRepository
        results = LibraryRepository.search_files_by_title("Biology Textbook")
        assert all(isinstance(r, CurriculumFile) for r in results)
        assert library_file in results

    def test_search_files_by_title_does_not_have_body_html(self, library_file):
        """CurriculumFile results must NOT have body_html (they are file assets, not lessons)."""
        from apps.curriculum.repositories import LibraryRepository
        results = LibraryRepository.search_files_by_title("Biology Textbook")
        for r in results:
            assert not hasattr(r, "body_html"), "Got a Lesson instead of CurriculumFile"
