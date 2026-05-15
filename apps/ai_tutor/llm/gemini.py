"""
apps/ai_tutor/llm/gemini.py
────────────────────────────
ConcreteStrategy: Google Gemini provider.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from decouple import config

from .base import LLMProvider

logger = logging.getLogger(__name__)


def _filter_schema(schema: dict) -> dict:
    """Recursively filter unsupported keys like 'default' from JSON schemas."""
    if not isinstance(schema, dict):
        return schema
    new_schema = {}
    for k, v in schema.items():
        if k == "default":
            continue
        if isinstance(v, dict):
            new_schema[k] = _filter_schema(v)
        elif isinstance(v, list):
            new_schema[k] = [_filter_schema(i) if isinstance(i, dict) else i for i in v]
        else:
            new_schema[k] = v
    return new_schema

class GeminiProvider(LLMProvider):
    """Calls Google Gemini using the google-generativeai SDK."""

    MODEL = "gemini-2.5-flash"

    @property
    def name(self) -> str:
        return self.MODEL

    @property
    def is_available(self) -> bool:
        return bool(config("GEMINI_API_KEY", default=""))

    def _get_client(self):
        import google.generativeai as genai
        genai.configure(api_key=config("GEMINI_API_KEY"))
        return genai

    async def complete(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        import google.generativeai as genai
        from google.generativeai.types import FunctionDeclaration, Tool

        self._get_client()  # configure API key

        gemini_tools = [
            FunctionDeclaration(
                name=t["name"],
                description=t.get("description", ""),
                parameters=_filter_schema({
                    "type": "object",
                    "properties": t.get("inputSchema", {}).get("properties", {}),
                    "required": t.get("inputSchema", {}).get("required", []),
                }),
            )
            for t in tools_schema
        ]

        model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=system_prompt,
            tools=[Tool(function_declarations=gemini_tools)] if gemini_tools else [],
        )

        # Convert to Gemini history format
        gemini_history = []
        last_user_msg = ""
        for m in messages:
            if m["role"] == "user":
                last_user_msg = m["content"]
                if gemini_history:
                    gemini_history.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant" and m.get("content"):
                gemini_history.append({"role": "model", "parts": [m["content"]]})

        chat = model.start_chat(history=gemini_history)
        response = await asyncio.to_thread(chat.send_message, last_user_msg)

        tool_calls = []
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append({"name": fc.name, "args": dict(fc.args)})

        text = response.text if not tool_calls else ""
        return text, tool_calls
