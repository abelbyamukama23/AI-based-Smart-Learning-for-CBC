"""
apps/ai_tutor/views.py — AI Tutor ViewSet (Refactored)
=======================================================
Design Patterns applied:
  • Service Layer — thread resolution, history building, and session
    persistence all delegated to TutorSessionService.
  • Facade Pattern — stream_generator is now a thin 30-line SSE adapter.
  • Thin Controller — AskViewSet.create() is pure HTTP plumbing.
"""

import json
import logging

from django.http import StreamingHttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response

from .agent import run_tutor_agent_stream
from .exceptions import ThreadNotFoundError
from .models import ChatThread
from .serializers import AskSerializer, ChatThreadSerializer, ChatThreadSummarySerializer
from .services import TutorSessionService

logger = logging.getLogger(__name__)


class ChatThreadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /api/v1/tutor/threads/        — Sidebar thread list.
    GET /api/v1/tutor/threads/{id}/   — Full thread with all interactions.

    N+1 fix: prefetch_related("interactions") is applied in both actions
    via get_queryset so the list never fires per-thread DB hits.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Prefetch, Q
        from .models import AISession
        
        queryset = ChatThread.objects.filter(learner=self.request.user)
        
        # Search functionality: matches title OR any message content within the thread
        q = self.request.query_params.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(interactions__query__icontains=q) |
                Q(interactions__response__icontains=q)
            ).distinct()

        return (
            queryset
            .prefetch_related(
                Prefetch(
                    "interactions",
                    queryset=AISession.objects.order_by("timestamp"),
                )
            )
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        return ChatThreadSummarySerializer if self.action == "list" else ChatThreadSerializer


class AskViewSet(viewsets.ViewSet):
    """
    POST /api/v1/tutor/ask/
    Body: { "query": "...", "thread_id": "<uuid|null>", "context_lesson_id": "<uuid|null>" }

    Returns a Server-Sent Events stream.  Thread management and session
    persistence are fully handled by TutorSessionService — this view is
    pure SSE streaming glue.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def create(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text        = serializer.validated_data["query"]
        thread_id         = serializer.validated_data.get("thread_id")
        context_lesson_id = serializer.validated_data.get("context_lesson_id")
        mode              = serializer.validated_data.get("mode", "default")
        user              = request.user

        logger.info(
            "AskViewSet: user=%s, thread=%s, mode=%s, query='%s...'",
            user.id, thread_id, mode, query_text[:60],
        )

        def stream_generator():
            import base64

            # ── 1. Resolve / create thread (Service Layer) ─────────────────────
            try:
                thread, created = TutorSessionService.resolve_thread(
                    str(thread_id) if thread_id else None, user, query_text
                )
            except ThreadNotFoundError as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            if created:
                yield f"data: {json.dumps({'type': 'thread_created', 'thread_id': str(thread.id), 'title': thread.title})}\n\n"

            # ── 2. Decode image (transient, never stored) ──────────────────────
            image_b64, image_mime = None, None
            image_file = request.FILES.get("image")
            if image_file:
                raw = image_file.read()
                image_b64  = base64.b64encode(raw).decode("utf-8")
                image_mime = image_file.content_type or "image/jpeg"
                del raw

            # ── 3. Build conversation history (Service Layer) ──────────────────
            history = TutorSessionService.build_history(thread)

            # ── 4. Stream agent output ─────────────────────────────────────────
            final_data = {}
            for chunk in run_tutor_agent_stream(
                user_id=str(user.id),
                query=query_text,
                context_lesson_id=str(context_lesson_id) if context_lesson_id else None,
                history=history,
                image_b64=image_b64,
                image_mime=image_mime,
                mode=mode,
            ):
                try:
                    data = json.loads(chunk)
                    if data.get("type") == "final":
                        final_data = data
                except Exception:
                    pass
                yield f"data: {chunk}\n\n"

            # ── 5. Persist interaction (Service Layer) ─────────────────────────
            if final_data:
                interaction = TutorSessionService.persist_interaction(
                    thread=thread,
                    user=user,
                    query=query_text,
                    final_data=final_data,
                    context_lesson_id=context_lesson_id,
                )
                yield f"data: {json.dumps({'type': 'saved', 'interaction_id': str(interaction.id), 'thread_id': str(thread.id)})}\n\n"

        response = StreamingHttpResponse(
            stream_generator(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
