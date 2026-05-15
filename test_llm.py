import os
import django
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")
django.setup()

import asyncio
from apps.ai_tutor.llm.gemini import GeminiProvider

async def main():
    provider = GeminiProvider()
    print("Testing GeminiProvider.stream_complete...")
    try:
        gen = provider.stream_complete(
            messages=[{"role": "user", "content": "hello"}],
            tools_schema=[],
            system_prompt="You are a helpful assistant."
        )
        async for chunk in gen:
            print("CHUNK:", chunk)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
