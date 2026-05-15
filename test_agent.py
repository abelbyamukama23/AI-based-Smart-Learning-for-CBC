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

from apps.ai_tutor.agent import run_tutor_agent_stream

# ---- Test parameters -------------------------------------------------------
TEST_USER_ID   = "00000000-0000-0000-0000-000000000001"  # fake UUID - profile fetch gracefully fails
TEST_QUERY     = "Explain photosynthesis for an S2 Biology learner."
TEST_LESSON_ID = None

SEP = "=" * 60
print(SEP)
print("CBC TutorAgent -- Live Test (DeepSeek)")
print(SEP)
print(f"Query: {TEST_QUERY}\n")

final_response = ""
print("Streaming response:")
for chunk in run_tutor_agent_stream(
    user_id=TEST_USER_ID,
    query=TEST_QUERY,
    context_lesson_id=TEST_LESSON_ID,
):
    print(".", end="", flush=True)
    try:
        import json
        data = json.loads(chunk)
        if data.get("type") == "final":
            final_response = data.get("content", "")
    except:
        pass

print("\n\n" + "-" * 60)
print("FINAL RESPONSE:")
print(final_response)
print("-" * 60)
