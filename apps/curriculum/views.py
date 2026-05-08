from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Subject, Level, Competency, Lesson
from .serializers import (
    SubjectSerializer,
    LevelSerializer,
    CompetencySerializer,
    LessonListSerializer,
    LessonDetailSerializer
)

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubjectSerializer

    def get_queryset(self):
        # Annotate with competency count and only return active subjects
        return Subject.objects.filter(is_active=True).annotate(competency_count=Count('competencies'))

    @action(detail=True, methods=['get'])
    def competencies(self, request, pk=None):
        """Get all competencies for a specific subject"""
        subject = self.get_object()
        competencies = subject.competencies.all()
        # Optional: Filter by level if provided in query params
        level_id = request.query_params.get('level_id')
        if level_id:
            competencies = competencies.filter(level_id=level_id)

        serializer = CompetencySerializer(competencies, many=True)
        return Response(serializer.data)

class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    pagination_class = None # Return all levels at once usually

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ['subject', 'class_level']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']

    def get_queryset(self):
        # Select related subject and class_level to avoid N+1 queries
        return Lesson.objects.select_related('subject', 'class_level').all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonListSerializer
