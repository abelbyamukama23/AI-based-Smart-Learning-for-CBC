from rest_framework import serializers
from .models import Subject, Level, Competency, Lesson, CurriculumFile

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


class CurriculumFileSerializer(serializers.ModelSerializer):
    """Library file serializer — used by the Library browser page."""
    subject_name     = serializers.CharField(source="subject.subject_name",   read_only=True, default="")
    class_level_name = serializers.CharField(source="class_level.level_name", read_only=True, default="")
    tag_list         = serializers.ListField(child=serializers.CharField(),    read_only=True)
    file_url         = serializers.SerializerMethodField()

    class Meta:
        model  = CurriculumFile
        fields = [
            "id", "title", "description", "file_type",
            "subject", "subject_name", "class_level", "class_level_name",
            "tags", "tag_list", "source", "is_indexed",
            "file_url", "created_at",
        ]

    def get_file_url(self, obj):
        """Return the full public URL for the file."""
        if not obj.file:
            return None
        try:
            url = obj.file.url
            if url.startswith("http"):
                return url
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(url)
            return url
        except Exception:
            return None
