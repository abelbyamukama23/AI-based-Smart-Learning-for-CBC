"""
apps/ai_tutor/views.py — AI Tutor ViewSet
==========================================
Uses TutorAgent (MCP + LLM Race: Gemini | DeepSeek | Claude) to answer
learner queries with curriculum-grounded, context-aware responses.
"""
import logging
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AISession
from .serializers import AISessionSerializer, AskSerializer
from .agent import run_tutor_agent

logger = logging.getLogger(__name__)


class AISessionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for the Mwalimu AI Tutor.

    Endpoints:
      POST   /api/v1/tutor/ask/              — Ask a question (creates AISession)
      GET    /api/v1/tutor/history/          — List this learner's session history
      GET    /api/v1/tutor/history/{id}/     — Retrieve a specific session
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Learners only see their own sessions
        return AISession.objects.filter(learner=self.request.user).select_related(
            "context_lesson"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return AskSerializer
        return AISessionSerializer

    def create(self, request, *args, **kwargs):
        """
        POST /api/v1/tutor/ask/
        Body: { "query": "...", "context_lesson_id": "<uuid-optional>" }

        Triggers the TutorAgent:
          1. Starts MCP server subprocess.
          2. Fires Gemini + DeepSeek + Claude simultaneously.
          3. Fastest response wins (others cancelled).
          4. Tool calls are executed via MCP server against curriculum DB.
          5. Final response is persisted as an AISession.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text = serializer.validated_data["query"]
        context_lesson_id = serializer.validated_data.get("context_lesson_id")

        # ── Run the AI Agent ──────────────────────────────────────────────────
        user_id = str(request.user.id)
        logger.info(
            f"TutorAgent invoked for user={user_id}, "
            f"lesson_ctx={context_lesson_id}, query='{query_text[:80]}...'"
        )

        response_text, is_out_of_scope, provider_used, tool_calls_log = run_tutor_agent(
            user_id=user_id,
            query=query_text,
            context_lesson_id=str(context_lesson_id) if context_lesson_id else None,
        )

        # ── Persist Session ───────────────────────────────────────────────────
        session = AISession.objects.create(
            learner=request.user,
            query=query_text,
            response=response_text,
            flagged_out_of_scope=is_out_of_scope,
            context_lesson_id=context_lesson_id,
            tool_calls_log=tool_calls_log,
            llm_provider_used=provider_used,
        )

        logger.info(
            f"AISession {session.id} created | provider={provider_used} | "
            f"out_of_scope={is_out_of_scope} | tools_called={len(tool_calls_log)}"
        )

        # ── Return Response ───────────────────────────────────────────────────
        response_serializer = AISessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
