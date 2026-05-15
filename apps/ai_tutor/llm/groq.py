"""
apps/ai_tutor/llm/groq.py
──────────────────────────
ConcreteStrategy: Groq provider (OpenAI-compatible, Llama 3 models).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from decouple import config

from .base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Calls Groq API using the OpenAI-compatible SDK."""

    MODEL = "llama-3.3-70b-versatile"
    BASE_URL = "https://api.groq.com/openai/v1"
    MAX_TOKENS = 1024

    @property
    def name(self) -> str:
        return f"groq-{self.MODEL}"

    @property
    def is_available(self) -> bool:
        return bool(config("GROQ_API_KEY", default=""))

    def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=config("GROQ_API_KEY"),
            base_url=self.BASE_URL,
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
        openai_tools = self.format_openai_tools(tools_schema)  # DRY: defined in base

        full_messages = [{"role": "system", "content": system_prompt}] + messages
        kwargs: dict = {
            "model": self.MODEL,
            "messages": full_messages,
            "max_tokens": self.MAX_TOKENS,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools
            kwargs["tool_choice"] = "auto"

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
