"""
apps/ai_tutor/llm/ollama.py
────────────────────────────
ConcreteStrategy: Local Ollama provider (OpenAI-compatible).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from decouple import config

from .base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Calls a locally running Ollama instance (OpenAI-compatible endpoint)."""

    @property
    def name(self) -> str:
        return f"ollama-{config('OLLAMA_MODEL', default='llama3.1')}"

    @property
    def is_available(self) -> bool:
        return config("USE_OLLAMA", default="false").lower() == "true"

    def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key="ollama",
            base_url=config("OLLAMA_BASE_URL", default="http://localhost:11434/v1"),
        )

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
        model_name = config("OLLAMA_MODEL", default="llama3.1")

        openai_tools = [
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

        full_messages = [{"role": "system", "content": system_prompt}] + messages
        kwargs: dict = {"model": model_name, "messages": full_messages}
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                })

        return msg.content or "", tool_calls
