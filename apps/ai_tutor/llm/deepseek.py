"""
apps/ai_tutor/llm/deepseek.py
──────────────────────────────
ConcreteStrategy: DeepSeek LLM provider (OpenAI-compatible SDK).

Supports optional vision input (image_b64 / image_mime) as DeepSeek-V3
accepts base64 image payloads in the user message content list.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, AsyncGenerator

from decouple import config

from .base import LLMProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):
    """Calls DeepSeek chat API using the OpenAI-compatible SDK."""

    MODEL = "deepseek-chat"
    BASE_URL = "https://api.deepseek.com/v1"
    MAX_TOKENS = 2048

    @property
    def name(self) -> str:
        return self.MODEL

    @property
    def is_available(self) -> bool:
        return bool(config("DEEPSEEK_API_KEY", default=""))

    @property
    def supports_vision(self) -> bool:
        return True  # DeepSeek-V3 accepts base64 image payloads

    def _get_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=config("DEEPSEEK_API_KEY"),
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

        # Attach image to the last user message when provided
        if image_b64 and image_mime:
            for i in range(len(full_messages) - 1, -1, -1):
                if full_messages[i]["role"] == "user" and isinstance(
                    full_messages[i]["content"], str
                ):
                    original_text = full_messages[i]["content"]
                    full_messages[i] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                            },
                            {"type": "text", "text": original_text},
                        ],
                    }
                    break

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

    async def stream_complete(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        client = self._get_client()
        openai_tools = self.format_openai_tools(tools_schema)

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        if image_b64 and image_mime:
            for i in range(len(full_messages) - 1, -1, -1):
                if full_messages[i]["role"] == "user" and isinstance(full_messages[i]["content"], str):
                    original_text = full_messages[i]["content"]
                    full_messages[i] = {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
                            {"type": "text", "text": original_text},
                        ],
                    }
                    break

        kwargs: dict = {
            "model": self.MODEL,
            "messages": full_messages,
            "max_tokens": self.MAX_TOKENS,
            "stream": True,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools
            kwargs["tool_choice"] = "auto"

        stream = await client.chat.completions.create(**kwargs)

        tool_calls_dict = {}
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # 1. Text chunks
            if delta.content:
                yield {"type": "chunk", "content": delta.content}
                
            # 2. Tool calls fragments
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    index = tc.index
                    if index not in tool_calls_dict:
                        tool_calls_dict[index] = {
                            "id": tc.id,
                            "name": tc.function.name if tc.function else "",
                            "arguments": ""
                        }
                    
                    if tc.function and tc.function.arguments:
                        tool_calls_dict[index]["arguments"] += tc.function.arguments

        # If we assembled tool calls, yield them at the very end
        if tool_calls_dict:
            final_tool_calls = []
            for idx in sorted(tool_calls_dict.keys()):
                tc = tool_calls_dict[idx]
                try:
                    args = json.loads(tc["arguments"])
                except Exception:
                    args = {}
                final_tool_calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "args": args,
                })
            yield {"type": "tool_calls", "tool_calls": final_tool_calls}
