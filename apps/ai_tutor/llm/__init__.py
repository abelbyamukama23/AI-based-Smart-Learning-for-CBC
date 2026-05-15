"""
apps/ai_tutor/llm/__init__.py
──────────────────────────────
Public surface of the LLM Strategy package.

Import from here, not from sub-modules, so internal restructuring
never breaks callers:
    from apps.ai_tutor.llm import LLMRace, DeepSeekProvider
"""

from .base import LLMProvider
from .claude import ClaudeProvider
from .deepseek import DeepSeekProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider
from .race import LLMRace

__all__ = [
    "LLMProvider",
    "DeepSeekProvider",
    "GeminiProvider",
    "GroqProvider",
    "ClaudeProvider",
    "OllamaProvider",
    "LLMRace",
]
