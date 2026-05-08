# -*- coding: utf-8 -*-
"""
Quick end-to-end test of the TutorAgent with DeepSeek.
Run from the project root:  python test_agent.py
"""
import os
import sys
import asyncio

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Bootstrap Django
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")

# Load .env values into os.environ before Django setup
from decouple import config
os.environ["DEEPSEEK_API_KEY"]  = config("DEEPSEEK_API_KEY",  default="")
os.environ["GEMINI_API_KEY"]    = config("GEMINI_API_KEY",    default="")
os.environ["ANTHROPIC_API_KEY"] = config("ANTHROPIC_API_KEY", default="")
os.environ["GROQ_API_KEY"]      = config("GROQ_API_KEY",      default="")
os.environ["USE_OLLAMA"]        = config("USE_OLLAMA",        default="false")

import django
django.setup()

from apps.ai_tutor.agent import run_tutor_agent

# ---- Test parameters -------------------------------------------------------
TEST_USER_ID   = "00000000-0000-0000-0000-000000000001"  # fake UUID - profile fetch gracefully fails
TEST_QUERY     = "Explain photosynthesis for an S2 Biology learner."
TEST_LESSON_ID = None

SEP = "=" * 60
print(SEP)
print("CBC TutorAgent -- Live Test (DeepSeek)")
print(SEP)
print(f"Query: {TEST_QUERY}\n")

response_text, is_out_of_scope, provider_used, tool_calls_log = run_tutor_agent(
    user_id=TEST_USER_ID,
    query=TEST_QUERY,
    context_lesson_id=TEST_LESSON_ID,
)

print(f"Provider that won the race : {provider_used}")
print(f"Flagged out of scope        : {is_out_of_scope}")
print(f"MCP Tools called            : {len(tool_calls_log)}")
if tool_calls_log:
    for tc in tool_calls_log:
        print(f"  Round {tc['round']} -> {tc['tool']}({tc['args']})")
print()
print("-" * 60)
print("RESPONSE:")
print(response_text)
print("-" * 60)
