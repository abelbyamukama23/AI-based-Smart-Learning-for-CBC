"""
apps/ai_tutor/llm/claude.py
────────────────────────────
ConcreteStrategy: Anthropic Claude provider.
"""

from __future__ import annotations

import logging
from typing import Optional

from decouple import config

from .base import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Calls Anthropic Claude API."""

    MODEL = "claude-3-5-haiku-20241022"
    MAX_TOKENS = 1024

    @property
    def name(self) -> str:
        return "claude-3-5-haiku"

    @property
    def is_available(self) -> bool:
        return bool(config("ANTHROPIC_API_KEY", default=""))

    def _get_client(self):
        import anthropic
        return anthropic.AsyncAnthropic(api_key=config("ANTHROPIC_API_KEY"))

    async def complete(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        client = self._get_client()

        anthropic_tools = [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": self.sanitize_schema(
                    t.get("inputSchema", {"type": "object", "properties": {}})
                ),
            }
            for t in tools_schema
        ]

        # Anthropic requires strict user/assistant alternation
        anthropic_messages = [
            {"role": m["role"], "content": m.get("content", "")}
            for m in messages
            if m["role"] in ("user", "assistant") and m.get("content")
        ]

        kwargs: dict = {
            "model": self.MODEL,
            "max_tokens": self.MAX_TOKENS,
            "system": system_prompt,
            "messages": anthropic_messages,
        }
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = await client.messages.create(**kwargs)

        tool_calls = []
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "args": block.input,
                })

        return "\n".join(text_parts), tool_calls
