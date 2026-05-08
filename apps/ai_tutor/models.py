import uuid
from django.db import models
from apps.accounts.models import User
from apps.curriculum.models import Lesson


class AISession(models.Model):
    """
    Represents a single query-response interaction with the AI Tutor (Mwalimu).

    Fields:
      - context_lesson: Optional lesson the learner was viewing when they asked.
      - tool_calls_log: JSON log of every MCP tool the agent called.
      - llm_provider_used: Which LLM won the race (gemini, deepseek, claude, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_sessions")
    query = models.TextField()
    response = models.TextField(null=True, blank=True)
    flagged_out_of_scope = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    kb_version = models.CharField(max_length=20, default="MCP-1.0")

    # New fields added for MCP Agent
    context_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_sessions",
        help_text="The lesson the learner was viewing when this question was asked.",
    )
    tool_calls_log = models.JSONField(
        default=list,
        blank=True,
        help_text="Log of MCP tool calls made by the agent during this session.",
    )
    llm_provider_used = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Which LLM provider won the race (gemini-1.5-flash, deepseek-chat, claude-3-5-haiku, mock).",
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"AI Session for {self.learner.username} at {self.timestamp} [{self.llm_provider_used}]"
