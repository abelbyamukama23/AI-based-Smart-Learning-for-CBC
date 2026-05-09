"""
apps/ai_tutor/views.py — AI Tutor ViewSet (Threaded)
======================================================
Endpoints:
  POST /api/v1/tutor/ask/           — Send a query; auto-creates or appends to a thread.
  GET  /api/v1/tutor/threads/       — List this learner's chat threads (sidebar).
  GET  /api/v1/tutor/threads/{id}/  — Retrieve a full thread with all interactions.
"""
import json
import logging

from django.http import StreamingHttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .agent import run_tutor_agent_stream
from .models import AISession, ChatThread
from .serializers import (
    AskSerializer,
    ChatThreadSerializer,
    ChatThreadSummarySerializer,
)

logger = logging.getLogger(__name__)


# ── Chat Thread ViewSet ────────────────────────────────────────────────────────
class ChatThreadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /api/v1/tutor/threads/        — Sidebar: list of threads (lightweight).
    GET /api/v1/tutor/threads/{id}/   — Full thread with all interaction turns.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(learner=self.request.user).prefetch_related(
            "interactions"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ChatThreadSummarySerializer
        return ChatThreadSerializer


# ── Ask ViewSet ────────────────────────────────────────────────────────────────
class AskViewSet(viewsets.ViewSet):
    """
    POST /api/v1/tutor/ask/
    Body: { "query": "...", "thread_id": "<uuid|null>", "context_lesson_id": "<uuid|null>" }

    - If thread_id is null  → creates a new ChatThread, returns thread_id in SSE stream.
    - If thread_id provided → appends interaction to existing thread.
    Streams SSE events for real-time UI feedback.
    """
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text        = serializer.validated_data["query"]
        thread_id         = serializer.validated_data.get("thread_id")
        context_lesson_id = serializer.validated_data.get("context_lesson_id")
        user              = request.user
        user_id           = str(user.id)

        logger.info(
            f"AskViewSet: user={user_id}, thread={thread_id}, query='{query_text[:60]}...'"
        )

        def stream_generator():
            import base64

            # ── 1. Resolve or create the thread ───────────────────────────────
            if thread_id:
                try:
                    thread = ChatThread.objects.get(id=thread_id, learner=user)
                except ChatThread.DoesNotExist:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Thread not found.'})}\n\n"
                    return
            else:
                title = query_text[:80] + ("..." if len(query_text) > 80 else "")
                thread = ChatThread.objects.create(learner=user, title=title)
                yield f"data: {json.dumps({'type': 'thread_created', 'thread_id': str(thread.id), 'title': thread.title})}\n\n"

            # ── 2. Decode image in memory (if provided) ───────────────────────
            image_b64 = None
            image_mime = None
            image_file = request.FILES.get("image")
            if image_file:
                raw = image_file.read()  # read into memory
                image_b64 = base64.b64encode(raw).decode("utf-8")
                image_mime = image_file.content_type or "image/jpeg"
                del raw  # discard immediately — not stored
                logger.info(f"Image received: {image_file.name}, mime={image_mime}")

            # ── 3. Build history from this specific thread ────────────────────
            past = AISession.objects.filter(thread=thread).order_by("timestamp")
            history_list = []
            for h in past:
                history_list.append({"role": "user", "content": h.query})
                if h.response:
                    history_list.append({"role": "assistant", "content": h.response})

            # ── 4. Run the agent and stream progress ──────────────────────────
            final_data = {}
            for chunk in run_tutor_agent_stream(
                user_id=user_id,
                query=query_text,
                context_lesson_id=str(context_lesson_id) if context_lesson_id else None,
                history=history_list,
                image_b64=image_b64,
                image_mime=image_mime,
            ):
                try:
                    data = json.loads(chunk)
                    if data.get("type") == "final":
                        final_data = data
                except Exception:
                    pass
                yield f"data: {chunk}\n\n"

            # ── 5. Persist the interaction turn ───────────────────────────────
            if final_data:
                interaction = AISession.objects.create(
                    thread=thread,
                    learner=user,
                    query=query_text,
                    response=final_data.get("content", ""),
                    flagged_out_of_scope=final_data.get("is_out_of_scope", False),
                    context_lesson_id=context_lesson_id,
                    tool_calls_log=final_data.get("tool_calls_log", []),
                    llm_provider_used=final_data.get("provider", ""),
                )
                thread.save()
                yield f"data: {json.dumps({'type': 'saved', 'interaction_id': str(interaction.id), 'thread_id': str(thread.id)})}\n\n"
                logger.info(
                    f"Interaction {interaction.id} saved → Thread {thread.id} | "
                    f"provider={interaction.llm_provider_used}"
                )

        response = StreamingHttpResponse(stream_generator(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
