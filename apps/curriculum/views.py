from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Subject, Level, Competency, Lesson, CurriculumFile
from .serializers import (
    SubjectSerializer,
    LevelSerializer,
    CompetencySerializer,
    LessonListSerializer,
    LessonDetailSerializer,
    CurriculumFileSerializer,
)

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubjectSerializer

    def get_queryset(self):
        return Subject.objects.filter(is_active=True).annotate(competency_count=Count('competencies'))

    @action(detail=True, methods=['get'])
    def competencies(self, request, pk=None):
        """Get all competencies for a specific subject"""
        subject = self.get_object()
        competencies = subject.competencies.all()
        level_id = request.query_params.get('level_id')
        if level_id:
            competencies = competencies.filter(level_id=level_id)
        serializer = CompetencySerializer(competencies, many=True)
        return Response(serializer.data)

class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    pagination_class = None

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ['subject', 'class_level']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']

    def get_queryset(self):
        return Lesson.objects.select_related('subject', 'class_level').all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonListSerializer


class CurriculumFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Library browser endpoint.
    GET /api/v1/curriculum/library/              → list all files (filterable)
    GET /api/v1/curriculum/library/{id}/         → file detail
    GET /api/v1/curriculum/library/?subject=Bio  → filter by subject name
    GET /api/v1/curriculum/library/?level=S1     → filter by class level
    GET /api/v1/curriculum/library/?type=PDF     → filter by file type
    GET /api/v1/curriculum/library/?q=photosyn   → keyword search
    """
    permission_classes  = [IsAuthenticated]
    serializer_class    = CurriculumFileSerializer
    filterset_fields    = ['file_type', 'subject', 'class_level']
    search_fields       = ['title', 'description', 'tags']
    ordering_fields     = ['title', 'created_at', 'file_type']
    ordering            = ['-created_at']

    def get_queryset(self):
        qs = CurriculumFile.objects.select_related('subject', 'class_level').all()

        # Extra convenience filters via query params
        subject_name = self.request.query_params.get('subject_name')
        level_name   = self.request.query_params.get('level_name')
        file_type    = self.request.query_params.get('type')

        if subject_name:
            qs = qs.filter(subject__subject_name__icontains=subject_name)
        if level_name:
            qs = qs.filter(class_level__level_name__iexact=level_name)
        if file_type:
            qs = qs.filter(file_type__iexact=file_type)

        return qs
