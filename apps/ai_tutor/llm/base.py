"""
apps/ai_tutor/llm/base.py
──────────────────────────
Abstract Strategy interface for LLM providers.

Design Pattern: Strategy Pattern
  • LLMProvider is the Strategy interface.
  • Each concrete provider (DeepSeek, Gemini, etc.) is a ConcreteStrategy.
  • LLMRace is the Context — it works with any LLMProvider without knowing
    which one it is.

Design Principle: Open/Closed Principle
  Adding a new LLM (e.g. Mistral) requires only writing a new class that
  extends LLMProvider — no existing code changes.

Design Principle: Liskov Substitution
  Every provider can be substituted for LLMProvider transparently.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator


class LLMProvider(ABC):
    """
    Abstract base class (Strategy interface) for all LLM providers.

    Each subclass wraps one external LLM API and translates the common
    message format into that API's native format.
    """

    # ── Identity ───────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier recorded in AISession.llm_provider_used."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        True if the required API key / service is configured.
        LLMRace skips providers where is_available is False.
        """
        ...

    # ── Core method ───────────────────────────────────────────────────────────

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        """
        Send a completion request to the LLM.

        Args:
            messages:      Conversation history (role/content dicts).
            tools_schema:  MCP tool definitions already sanitised for this API.
            system_prompt: The tutor system instruction string.
            image_b64:     Optional base64-encoded image bytes.
            image_mime:    MIME type of the image (e.g. 'image/jpeg').

        Returns:
            (response_text, tool_calls)
            • response_text — the model's text reply (empty string when the model
              chose to call a tool instead).
            • tool_calls    — list of {"id", "name", "args"} dicts (empty list
              when the model gave a text reply directly).
        """
        ...

    async def stream_complete(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a completion request to the LLM.
        By default, falls back to the non-streaming `complete` method for providers
        that do not implement native streaming, yielding the entire text at once.
        """
        text, tool_calls = await self.complete(
            messages, tools_schema, system_prompt, 
            image_b64=image_b64, image_mime=image_mime
        )
        if tool_calls:
            yield {"type": "tool_calls", "tool_calls": tool_calls}
        else:
            yield {"type": "chunk", "content": text}

    # ── Schema sanitization helper (shared by all providers) ──────────────────

    _SCHEMA_BLOCKED_FIELDS: frozenset[str] = frozenset(
        {"default", "title", "$schema", "examples", "$defs"}
    )

    @classmethod
    def sanitize_schema(cls, schema) -> dict:
        """
        Recursively strip JSON-Schema keys that OpenAI-compatible and Anthropic
        APIs reject.  Defined once here — all providers inherit it (DRY).
        """
        if not isinstance(schema, dict):
            return schema
        cleaned = {k: v for k, v in schema.items() if k not in cls._SCHEMA_BLOCKED_FIELDS}
        if "properties" in cleaned and isinstance(cleaned["properties"], dict):
            cleaned["properties"] = {
                k: cls.sanitize_schema(v) for k, v in cleaned["properties"].items()
            }
        if "items" in cleaned:
            cleaned["items"] = cls.sanitize_schema(cleaned["items"])
        return cleaned

    def format_openai_tools(self, tools_schema: list[dict]) -> list[dict]:
        """
        Convert MCP tool schema to OpenAI function-calling format.

        DRY: Defined once here, inherited by all OpenAI-compatible providers
        (DeepSeek, Groq, Claude via openai-compat).  Gemini and Ollama use
        their own native tool formats and do not call this method.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": self.sanitize_schema(
                        t.get("inputSchema", {"type": "object", "properties": {}})
                    ),
                },
            }
            for t in tools_schema
        ]

    @property
    def supports_vision(self) -> bool:
        """
        ISP fix: True only for providers that genuinely support image inputs.

        LLMRace uses this to skip non-vision providers when an image is attached,
        preventing silent image-drop bugs.  Override to True in DeepSeek and Gemini.
        """
        return False
