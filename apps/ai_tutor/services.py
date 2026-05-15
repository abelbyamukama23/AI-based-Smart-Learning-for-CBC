"""
apps/ai_tutor/services.py
──────────────────────────
Service Layer for the AI Tutor domain.

Design Patterns applied:
  • Service Layer — ChatThread resolution, history building, and session
    persistence are no longer inline inside the view's stream_generator.
  • Unit of Work  — thread creation and session persistence use save_points.
  • SRP           — TutorSessionService handles one thing: managing AI sessions.

The view becomes a pure SSE-streaming adapter.
"""

from __future__ import annotations

import logging
from typing import Optional

from .exceptions import ThreadNotFoundError
from .models import AISession, ChatThread

logger = logging.getLogger(__name__)


class TutorSessionService:
    """
    Manages ChatThread resolution and AISession persistence.

    The view calls into these methods; the agent loop never touches the DB
    directly (Dependency Inversion).
    """

    @staticmethod
    def resolve_thread(thread_id: Optional[str], user, query_text: str) -> tuple[ChatThread, bool]:
        """
        Resolve the target ChatThread.

        Args:
            thread_id:   UUID string of an existing thread, or None to create one.
            user:        The authenticated User making the request.
            query_text:  Used as the auto-generated title when creating a new thread.

        Returns:
            (thread, created)  — created is True when a new thread was made.

        Raises:
            ThreadNotFoundError: If thread_id is given but not found for this user.
        """
        if thread_id:
            try:
                thread = ChatThread.objects.get(id=thread_id, learner=user)
                return thread, False
            except ChatThread.DoesNotExist:
                raise ThreadNotFoundError(
                    f"Thread {thread_id} not found for user {user.id}."
                )

        title = query_text[:80] + ("..." if len(query_text) > 80 else "")
        thread = ChatThread.objects.create(learner=user, title=title)
        return thread, True

    @staticmethod
    def build_history(thread: ChatThread) -> list[dict]:
        """
        Build the conversation history list for the agent.

        Returns alternating user/assistant message dicts pulled from all
        AISession rows in the thread, ordered by timestamp ascending.
        """
        # Limit to the last 10 interactions (20 messages) to save tokens (Sliding Window)
        past_qs = (
            AISession.objects
            .filter(thread=thread)
            .order_by("-timestamp")[:10]
        )
        
        # We must evaluate the queryset and reverse it to maintain chronological order
        past = list(past_qs)
        past.reverse()

        history = []
        for session in past:
            history.append({"role": "user", "content": session.query})
            if session.response:
                history.append({"role": "assistant", "content": session.response})
        return history

    @staticmethod
    def persist_interaction(
        *,
        thread: ChatThread,
        user,
        query: str,
        final_data: dict,
        context_lesson_id=None,
    ) -> AISession:
        """
        Persist one complete query-response turn as an AISession row.

        Args:
            thread:            The parent ChatThread.
            user:              The authenticated User.
            query:             The learner's question text.
            final_data:        The 'final' SSE event payload from the agent.
            context_lesson_id: Optional UUID of the lesson the learner was viewing.

        Returns:
            The newly created AISession instance.
        """
        interaction = AISession.objects.create(
            thread=thread,
            learner=user,
            query=query,
            response=final_data.get("content", ""),
            flagged_out_of_scope=final_data.get("is_out_of_scope", False),
            context_lesson_id=context_lesson_id,
            tool_calls_log=final_data.get("tool_calls_log", []),
            llm_provider_used=final_data.get("provider", ""),
        )
        # Update thread.updated_at so the sidebar sorts correctly
        thread.save(update_fields=["updated_at"])

        logger.info(
            "Interaction %s saved → Thread %s | provider=%s",
            interaction.id,
            thread.id,
            interaction.llm_provider_used,
        )
        return interaction
