"""
apps/curriculum/views.py
─────────────────────────
HTTP adapters only — query logic delegated to curriculum/repositories.py.

Design Pattern: Repository Pattern
  Views call repository methods; they never construct QuerySets themselves.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .repositories import CompetencyRepository, LessonRepository, LibraryRepository, SubjectRepository
from .serializers import (
    CompetencySerializer,
    CurriculumFileSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
    LevelSerializer,
    SubjectSerializer,
)
from .models import Level


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubjectSerializer

    def get_queryset(self):
        return SubjectRepository.list_active()

    @action(detail=True, methods=["get"])
    def competencies(self, request, pk=None):
        """GET /api/v1/curriculum/subjects/{id}/competencies/?level_id=<uuid>"""
        subject = self.get_object()
        level_id = request.query_params.get("level_id")
        qs = subject.competencies.all()
        if level_id:
            qs = qs.filter(level_id=level_id)
        return Response(CompetencySerializer(qs, many=True).data)


class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    pagination_class = None


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ["subject", "class_level"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]

    def get_queryset(self):
        return LessonRepository.list_all()

    def get_serializer_class(self):
        return LessonDetailSerializer if self.action == "retrieve" else LessonListSerializer


class CurriculumFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Library browser.
    GET /api/v1/curriculum/library/              → list all files (filterable)
    GET /api/v1/curriculum/library/{id}/         → file detail
    """
    permission_classes  = [IsAuthenticated]
    serializer_class    = CurriculumFileSerializer
    filterset_fields    = ["file_type", "subject", "class_level"]
    search_fields       = ["title", "description", "tags"]
    ordering_fields     = ["title", "created_at", "file_type"]
    ordering            = ["-created_at"]

    def get_queryset(self):
        qs = LibraryRepository.base_queryset()

        # Extra convenience filters via query params
        subject_name = self.request.query_params.get("subject_name")
        level_name   = self.request.query_params.get("level_name")
        file_type    = self.request.query_params.get("type")

        if subject_name:
            qs = qs.filter(subject__subject_name__icontains=subject_name)
        if level_name:
            qs = qs.filter(class_level__level_name__iexact=level_name)
        if file_type:
            qs = qs.filter(file_type__iexact=file_type)

        return qs
