"""
apps/ai_tutor/serializers.py
"""
from rest_framework import serializers
from .models import AISession, ChatThread


class AISessionSerializer(serializers.ModelSerializer):
    """A single turn (Q&A) within a chat thread."""
    class Meta:
        model = AISession
        fields = [
            "id",
            "query",
            "response",
            "flagged_out_of_scope",
            "timestamp",
            "kb_version",
            "context_lesson",
            "tool_calls_log",
            "llm_provider_used",
        ]
        read_only_fields = fields


class ChatThreadSerializer(serializers.ModelSerializer):
    """A full conversation thread with all its interactions embedded."""
    interactions = AISessionSerializer(many=True, read_only=True)
    interaction_count = serializers.IntegerField(source="interactions.count", read_only=True)

    class Meta:
        model = ChatThread
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "interaction_count",
            "interactions",
        ]
        read_only_fields = fields


class ChatThreadSummarySerializer(serializers.ModelSerializer):
    """Lightweight summary for the sidebar thread list (no embedded interactions)."""
    interaction_count = serializers.IntegerField(source="interactions.count", read_only=True)
    last_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "interaction_count",
            "last_message_preview",
        ]
        read_only_fields = fields

    def get_last_message_preview(self, obj):
        last = obj.interactions.last()
        if last and last.response:
            return last.response[:120] + ("..." if len(last.response) > 120 else "")
        return ""


class AskSerializer(serializers.Serializer):
    """Input serializer for POST /api/v1/tutor/ask/"""
    query = serializers.CharField(
        required=True,
        help_text="The question or topic the learner wants to ask Mwalimu.",
    )
    thread_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "UUID of the active chat thread. If omitted, a new thread is created."
        ),
    )
    context_lesson_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Optional UUID of the lesson the learner is currently viewing."
        ),
    )
