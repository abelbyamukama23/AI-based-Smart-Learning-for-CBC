import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")

from mcp_server.server import mcp

import asyncio
async def test():
    tools = await mcp.list_tools()
    print("TOOLS:", tools[0].name)
    try:
        res = await mcp.call_tool("search_curriculum", {"query": "photosynthesis"})
        print("CALL RES:", type(res), res)
    except Exception as e:
        print("CALL ERROR:", e)

asyncio.run(test())
