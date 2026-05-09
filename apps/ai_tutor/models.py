import uuid
from django.db import models
from apps.accounts.models import User
from apps.curriculum.models import Lesson


class ChatThread(models.Model):
    """
    Represents a single conversation session between a learner and Mwalimu.
    One thread contains many AISession interactions (turns).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_threads")
    title = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Auto-generated title from the first question in the thread.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Thread [{self.learner.username}]: {self.title or '(untitled)'}"


class AISession(models.Model):
    """
    Represents a single query-response interaction (turn) with Mwalimu.
    Many AISession rows belong to one ChatThread.

    Fields:
      - thread:           The parent conversation thread.
      - context_lesson:  Optional lesson the learner was viewing when they asked.
      - tool_calls_log:  JSON log of every MCP tool the agent called.
      - llm_provider_used: Which LLM won the race (gemini, deepseek, claude, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="interactions",
        null=True,
        blank=True,
        help_text="The parent chat thread this interaction belongs to.",
    )
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_sessions")
    query = models.TextField()
    response = models.TextField(null=True, blank=True)
    flagged_out_of_scope = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    kb_version = models.CharField(max_length=20, default="MCP-1.0")

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
        ordering = ["timestamp"]

    def __str__(self):
        thread_info = f"Thread:{self.thread_id}" if self.thread_id else "No Thread"
        return f"[{thread_info}] {self.learner.username} @ {self.timestamp}"
