"""
tests/test_ai_tutor_service.py
────────────────────────────────
Unit & integration tests for the AI Tutor service layer.

Covers:
  - TutorSessionService.resolve_thread()
  - TutorSessionService.build_history()
  - TutorSessionService.persist_interaction()
  - LLMProvider.sanitize_schema()           — pure logic, unit test
  - LLMProvider.format_openai_tools()       — pure logic, unit test
  - LLMRace Null Object (no providers)      — pure logic, unit test

Run:
    pytest tests/test_ai_tutor_service.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests — LLMProvider base class (pure logic, no DB, no network)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMProviderBase:

    @pytest.mark.unit
    def test_sanitize_schema_strips_blocked_fields(self):
        """sanitize_schema removes 'default', 'title', '$schema', etc. recursively."""
        from apps.ai_tutor.llm.base import LLMProvider

        raw = {
            "type": "object",
            "title": "Should be removed",
            "$schema": "http://...",
            "properties": {
                "query": {
                    "type": "string",
                    "title": "Also removed",
                    "default": "removed too",
                    "description": "Kept",
                }
            },
        }
        cleaned = LLMProvider.sanitize_schema(raw)

        assert "title" not in cleaned
        assert "$schema" not in cleaned
        assert "title" not in cleaned["properties"]["query"]
        assert "default" not in cleaned["properties"]["query"]
        assert cleaned["properties"]["query"]["description"] == "Kept"
        assert cleaned["type"] == "object"

    @pytest.mark.unit
    def test_format_openai_tools_produces_correct_shape(self):
        """format_openai_tools converts MCP schema to the OpenAI function format."""
        from apps.ai_tutor.llm.deepseek import DeepSeekProvider  # Concrete so we can instantiate

        provider = DeepSeekProvider()
        mcp_tools = [
            {
                "name": "search_library_rag",
                "description": "Search the curriculum library",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "title": "Query"},
                    },
                    "required": ["query"],
                },
            }
        ]
        result = provider.format_openai_tools(mcp_tools)

        assert len(result) == 1
        tool = result[0]
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "search_library_rag"
        # title should be stripped by sanitize_schema
        assert "title" not in tool["function"]["parameters"]["properties"]["query"]

    @pytest.mark.unit
    def test_deepseek_supports_vision_is_true(self):
        from apps.ai_tutor.llm.deepseek import DeepSeekProvider
        assert DeepSeekProvider().supports_vision is True

    @pytest.mark.unit
    def test_groq_supports_vision_is_false(self):
        from apps.ai_tutor.llm.groq import GroqProvider
        assert GroqProvider().supports_vision is False

    @pytest.mark.unit
    def test_gemini_supports_vision_defaults_false(self):
        """Gemini uses its own vision path — the property is not overridden yet."""
        from apps.ai_tutor.llm.gemini import GeminiProvider
        assert GeminiProvider().supports_vision is False


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests — LLMRace Null Object
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMRaceNullObject:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_mock_response_when_no_providers_configured(self):
        """When no providers are available, a safe mock string is returned (Null Object)."""
        from apps.ai_tutor.llm.race import LLMRace

        # All providers report is_available=False
        fake_provider = MagicMock()
        fake_provider.is_available = False
        race = LLMRace([fake_provider])

        text, tool_calls, provider_name = await race.run(
            messages=[{"role": "user", "content": "Hello"}],
            tools_schema=[],
            system_prompt="You are a tutor.",
        )

        assert "No LLM API keys" in text
        assert tool_calls == []
        assert provider_name == "mock"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_race_uses_primary_provider_first(self):
        """Primary provider is tried first; fallback is not called if primary succeeds."""
        from apps.ai_tutor.llm.race import LLMRace
        from apps.ai_tutor.llm.base import LLMProvider

        primary = MagicMock(spec=LLMProvider)
        primary.is_available = True
        primary.name = "primary"
        primary.complete = AsyncMock(return_value=("Hello!", []))

        fallback = MagicMock(spec=LLMProvider)
        fallback.is_available = True
        fallback.name = "fallback"
        fallback.complete = AsyncMock(return_value=("Fallback response", []))

        race = LLMRace([primary, fallback])
        text, _, name = await race.run(
            [{"role": "user", "content": "Hi"}], [], "Be a tutor."
        )

        assert text == "Hello!"
        assert name == "primary"
        fallback.complete.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Integration tests — TutorSessionService
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def learner(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        username="testlearner",
        email="learner@test.ug",
        password="pass",
        role="LEARNER",
    )


@pytest.fixture
def thread(db, learner):
    from apps.ai_tutor.models import ChatThread
    return ChatThread.objects.create(learner=learner, title="My first thread")


@pytest.mark.django_db
class TestTutorSessionServiceResolveThread:

    def test_creates_new_thread_when_no_id_given(self, learner):
        from apps.ai_tutor.services import TutorSessionService
        thread, created = TutorSessionService.resolve_thread(None, learner, "What is osmosis?")
        assert created is True
        assert thread.learner == learner
        assert "What is osmosis" in thread.title

    def test_title_truncated_at_80_chars(self, learner):
        from apps.ai_tutor.services import TutorSessionService
        long_query = "A" * 100
        thread, created = TutorSessionService.resolve_thread(None, learner, long_query)
        assert len(thread.title) <= 83   # 80 chars + "..."
        assert thread.title.endswith("...")

    def test_resolves_existing_thread_by_id(self, learner, thread):
        from apps.ai_tutor.services import TutorSessionService
        found, created = TutorSessionService.resolve_thread(str(thread.id), learner, "irrelevant")
        assert created is False
        assert found.pk == thread.pk

    def test_raises_thread_not_found_for_wrong_user(self, learner, thread, db):
        from apps.accounts.models import User
        from apps.ai_tutor.exceptions import ThreadNotFoundError
        from apps.ai_tutor.services import TutorSessionService

        other_user = User.objects.create_user(
            username="other", email="other@test.ug", password="pass", role="LEARNER"
        )
        with pytest.raises(ThreadNotFoundError):
            TutorSessionService.resolve_thread(str(thread.id), other_user, "query")


@pytest.mark.django_db
class TestTutorSessionServiceBuildHistory:

    def test_empty_history_for_new_thread(self, thread):
        from apps.ai_tutor.services import TutorSessionService
        history = TutorSessionService.build_history(thread)
        assert history == []

    def test_history_contains_alternating_user_assistant_entries(self, thread, learner):
        from apps.ai_tutor.models import AISession
        from apps.ai_tutor.services import TutorSessionService

        AISession.objects.create(
            thread=thread,
            learner=learner,
            query="What is osmosis?",
            response="Osmosis is the movement of water...",
        )
        history = TutorSessionService.build_history(thread)

        assert history[0] == {"role": "user", "content": "What is osmosis?"}
        assert history[1] == {"role": "assistant", "content": "Osmosis is the movement of water..."}

    def test_history_skips_empty_responses(self, thread, learner):
        """Sessions with no response (interrupted) don't add an empty assistant turn."""
        from apps.ai_tutor.models import AISession
        from apps.ai_tutor.services import TutorSessionService

        AISession.objects.create(
            thread=thread,
            learner=learner,
            query="Quick question",
            response="",  # empty — no AI response stored
        )
        history = TutorSessionService.build_history(thread)

        assert len(history) == 1                        # Only the user message
        assert history[0]["role"] == "user"


@pytest.mark.django_db
class TestTutorSessionServicePersistInteraction:

    def test_persists_session_to_db(self, thread, learner):
        from apps.ai_tutor.models import AISession
        from apps.ai_tutor.services import TutorSessionService

        final_data = {
            "content": "Osmosis is...",
            "provider": "deepseek-chat",
            "is_out_of_scope": False,
            "tool_calls_log": [],
        }
        session = TutorSessionService.persist_interaction(
            thread=thread,
            user=learner,
            query="What is osmosis?",
            final_data=final_data,
        )

        assert AISession.objects.filter(pk=session.pk).exists()
        assert session.response == "Osmosis is..."
        assert session.llm_provider_used == "deepseek-chat"
        assert session.flagged_out_of_scope is False

    def test_persist_updates_thread_updated_at(self, thread, learner):
        """persist_interaction touches thread.updated_at for sidebar ordering."""
        import time
        from django.utils import timezone
        from apps.ai_tutor.services import TutorSessionService

        original_updated_at = thread.updated_at
        time.sleep(0.01)   # Ensure timestamp changes

        TutorSessionService.persist_interaction(
            thread=thread,
            user=learner,
            query="Hello",
            final_data={"content": "Hi!", "provider": "gemini", "is_out_of_scope": False, "tool_calls_log": []},
        )

        thread.refresh_from_db()
        assert thread.updated_at > original_updated_at
