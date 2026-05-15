"""
apps/ai_tutor/llm/race.py
──────────────────────────
LLMRace — Context class in the Strategy Pattern.

Design Patterns applied:
  • Strategy Pattern  — LLMRace works with any list of LLMProvider instances.
  • Template Method   — try primary first; race the rest on failure.
  • Null Object       — when no providers are configured, a mock response is
    returned rather than raising an exception.

Design Principle: Open/Closed
  Adding a new provider or changing the race strategy requires only changes
  here and in the provider list — TutorAgent never needs to change.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, AsyncGenerator

from ..exceptions import AllProvidersFailedError
from .base import LLMProvider

logger = logging.getLogger(__name__)

# Mock text returned when zero providers are configured (Null Object pattern)
_NO_PROVIDERS_MSG = (
    "[Mock] No LLM API keys are configured. "
    "Please set at least one of DEEPSEEK_API_KEY, GEMINI_API_KEY, "
    "ANTHROPIC_API_KEY, or GROQ_API_KEY in your .env file."
)


class LLMRace:
    """
    Context that executes a provider race strategy.

    Strategy:
      1. Try the primary provider (index 0) first — it typically has
         the best speed/quality for this application (DeepSeek).
      2. If the primary fails, fire all remaining available providers
         concurrently with asyncio.as_completed — first to respond wins,
         others are cancelled.
      3. If all fail, raise AllProvidersFailedError.
    """

    def __init__(self, providers: list[LLMProvider]):
        """
        Args:
            providers: Ordered list of strategies.  The first available
                       provider is treated as the primary (tried synchronously
                       before the race starts).
        """
        self._all_providers = providers

    @property
    def _available(self) -> list[LLMProvider]:
        """Returns only the providers whose is_available flag is True."""
        return [p for p in self._all_providers if p.is_available]

    async def run(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> tuple[str, list[dict], str]:
        """
        Execute the race.

        Returns:
            (response_text, tool_calls, provider_name)

        Raises:
            AllProvidersFailedError: When every configured provider fails.
        """
        available = self._available

        if not available:
            logger.warning("No LLM providers configured — returning mock response.")
            return _NO_PROVIDERS_MSG, [], "mock"

        # ── 1. Try primary provider first ──────────────────────────────────────
        primary = available[0]
        try:
            text, tool_calls = await primary.complete(
                messages, tools_schema, system_prompt,
                image_b64=image_b64, image_mime=image_mime,
            )
            logger.info("LLM primary provider responded: %s", primary.name)
            return text, tool_calls, primary.name
        except Exception as primary_err:
            logger.warning(
                "Primary provider %s failed (%s) — racing fallbacks.",
                primary.name, primary_err,
            )

        # ── 2. Race the remaining providers ───────────────────────────────────
        fallbacks = available[1:]
        if not fallbacks:
            raise AllProvidersFailedError(
                f"Primary provider {primary.name} failed and no fallbacks are configured."
            )

        tasks = [
            asyncio.create_task(
                provider.complete(
                    messages, tools_schema, system_prompt,
                    image_b64=image_b64, image_mime=image_mime,
                ),
                name=provider.name,
            )
            for provider in fallbacks
        ]

        errors: list[str] = []
        for coro in asyncio.as_completed(tasks):
            try:
                text, tool_calls = await coro
                # Cancel remaining in-flight tasks
                for t in tasks:
                    if not t.done():
                        t.cancel()
                winning_name = next(
                    (p.name for p in fallbacks if t.get_name() == p.name
                     for t in tasks if t.done() and not t.cancelled()),
                    "fallback"
                )
                logger.info("LLM race won by fallback: %s", winning_name)
                return text, tool_calls, winning_name
            except Exception as e:
                errors.append(str(e))
                logger.error("LLM fallback task failed: %s", e)

        raise AllProvidersFailedError(
            f"All LLM providers failed: {' | '.join(errors)}"
        )

    async def stream_run(
        self,
        messages: list[dict],
        tools_schema: list[dict],
        system_prompt: str,
        *,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Execute the primary provider in streaming mode.
        If it fails, currently falls back to nothing (streaming race is complex).
        In production, we would catch the error and stream from a fallback.
        """
        available = self._available

        if not available:
            logger.warning("No LLM providers configured — returning mock response.")
            yield {"type": "chunk", "content": _NO_PROVIDERS_MSG}
            return

        primary = available[0]
        chunks_yielded = 0
        try:
            generator = primary.stream_complete(
                messages, tools_schema, system_prompt,
                image_b64=image_b64, image_mime=image_mime,
            )
            async for chunk in generator:
                yield chunk
                chunks_yielded += 1
        except Exception as primary_err:
            logger.error("Primary provider %s failed during stream: %s", primary.name, primary_err)
            
            if chunks_yielded == 0 and len(available) > 1:
                fallback = available[1]
                logger.info("Falling back to %s", fallback.name)
                
                # Try the fallback provider
                try:
                    fallback_gen = fallback.stream_complete(
                        messages, tools_schema, system_prompt,
                        image_b64=image_b64, image_mime=image_mime,
                    )
                    async for chunk in fallback_gen:
                        yield chunk
                except Exception as fallback_err:
                    logger.error("Fallback provider %s also failed: %s", fallback.name, fallback_err)
                    yield {"type": "chunk", "content": f"\n\n[Error: Both {primary.name} and {fallback.name} failed to respond. Please try again.]"}
            else:
                # We already yielded partial output, so appending a new stream might look messy
                yield {"type": "chunk", "content": f"\n\n[Error: Connection to {primary.name} was lost mid-response. Please click Retry.]"}
