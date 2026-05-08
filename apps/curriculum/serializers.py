from rest_framework import serializers
from .models import Subject, Level, Competency, Lesson

class SubjectSerializer(serializers.ModelSerializer):
    competency_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'subject_name', 'is_active', 'competency_count']

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'level_name', 'sort_order']

class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = ['id', 'subject', 'level', 'competency_name', 'description']

class LessonListSerializer(serializers.ModelSerializer):
    """Lighter serializer for lists (excludes body_html)"""
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'subject', 'class_level', 'source', 'is_downloadable', 'created_at']

class LessonDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer with body_html and competencies"""
    competencies = CompetencySerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'subject', 'class_level', 
            'competencies', 'source', 'is_downloadable', 'file_size_kb', 
            'body_html', 'image', 'video_url', 'video_file', 'created_at', 'modified_at'
        ]
