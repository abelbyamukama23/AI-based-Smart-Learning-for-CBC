import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")

import django
django.setup()

from apps.curriculum.rag_service import search_library, compile_lesson, warm_up_rag

print("Warming up RAG...")
warm_up_rag()
print("Warm up complete.")

print("Testing search_library...")
try:
    results = search_library("photosynthesis", n_results=2)
    print(f"Results: {len(results)}")
    if results:
        print("First result title:", results[0].get('title'))
except Exception as e:
    print("Error in search_library:", e)

print("Testing compile_lesson...")
try:
    if results:
        lesson = compile_lesson(results[0].get('title'), "photosynthesis", [r['excerpt'] for r in results])
        print("Compile lesson success. Keys:", lesson.keys())
    else:
        print("No results to compile from.")
except Exception as e:
    print("Error in compile_lesson:", e)
