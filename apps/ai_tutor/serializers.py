from rest_framework import serializers
from .models import AISession


class AISessionSerializer(serializers.ModelSerializer):
    """Read serializer for returning AI session history and responses."""
    class Meta:
        model = AISession
        fields = [
            "id",
            "learner",
            "query",
            "response",
            "flagged_out_of_scope",
            "timestamp",
            "kb_version",
            "context_lesson",
            "tool_calls_log",
            "llm_provider_used",
        ]
        read_only_fields = [
            "id",
            "learner",
            "response",
            "flagged_out_of_scope",
            "timestamp",
            "kb_version",
            "tool_calls_log",
            "llm_provider_used",
        ]


class AskSerializer(serializers.Serializer):
    """Input serializer for POST /api/v1/tutor/ask/"""
    query = serializers.CharField(
        required=True,
        help_text="The question or topic the learner wants to ask Mwalimu.",
    )
    context_lesson_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Optional UUID of the lesson the learner is currently viewing. "
            "When provided, Mwalimu uses it for context-aware responses."
        ),
    )
