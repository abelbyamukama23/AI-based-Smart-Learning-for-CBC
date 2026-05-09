"""
apps/ai_tutor/agent.py — TutorAgent: AI Agent Loop with MCP + LLM Race Pattern
=================================================================================
Architecture:
  1. Start the MCP server (mcp_server/server.py) as a stdio subprocess.
  2. Fetch learner context via MCP resources.
  3. Fire the same prompt + tool schema at THREE LLMs simultaneously:
       - Google Gemini (gemini-1.5-flash)
       - DeepSeek       (deepseek-chat via OpenAI-compatible API)
       - Anthropic Claude (claude-3-5-haiku)
       - Groq           (llama3 via OpenAI-compatible API)
       - Ollama         (local open source models)
  4. The first LLM to respond wins — others are cancelled (asyncio race).
  5. If the winning LLM requested MCP tool calls, execute them and loop.
  6. Return (final_text, is_out_of_scope, provider_used).

Dependencies:
    pip install mcp google-generativeai anthropic openai
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional
from decouple import config

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
# agent.py lives at:  CBC/apps/ai_tutor/agent.py
# So we go up 3 levels:  ai_tutor/ → apps/ → CBC/ (project root)
_THIS_FILE   = os.path.abspath(__file__)                          # .../CBC/apps/ai_tutor/agent.py
_TUTOR_DIR   = os.path.dirname(_THIS_FILE)                        # .../CBC/apps/ai_tutor/
_APPS_DIR    = os.path.dirname(_TUTOR_DIR)                        # .../CBC/apps/
PROJECT_ROOT = os.path.dirname(_APPS_DIR)                         # .../CBC/
MCP_SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "mcp_server", "server.py")

# ── LLM Clients (lazy-initialised) ────────────────────────────────────────────
def _get_gemini_client():
    import google.generativeai as genai
    api_key = config("GEMINI_API_KEY", default="")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    genai.configure(api_key=api_key)
    return genai

def _get_deepseek_client():
    from openai import AsyncOpenAI
    api_key = config("DEEPSEEK_API_KEY", default="")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not configured")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )

def _get_groq_client():
    from openai import AsyncOpenAI
    api_key = config("GROQ_API_KEY", default="")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

def _get_ollama_client():
    from openai import AsyncOpenAI
    base_url = config("OLLAMA_BASE_URL", default="http://localhost:11434/v1")
    return AsyncOpenAI(
        api_key="ollama", # Ollama doesn't require a real API key
        base_url=base_url,
    )

def _get_claude_client():
    import anthropic
    api_key = config("ANTHROPIC_API_KEY", default="")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return anthropic.AsyncAnthropic(api_key=api_key)


# ════════════════════════════════════════════════════════════════════════════════
# MCP Client Helper
# ════════════════════════════════════════════════════════════════════════════════
async def _get_mcp_tools_and_session():
    """
    Start MCP server subprocess and return (session, tools_schema, read, write).
    Caller is responsible for cleanup.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_SCRIPT],
        env=None,
    )
    return server_params


async def _call_mcp_tool(session, tool_name: str, tool_args: dict) -> str:
    """Execute a single MCP tool call and return the result as a string."""
    result = await session.call_tool(tool_name, tool_args)
    # result.content is a list of TextContent / ImageContent
    texts = [c.text for c in result.content if hasattr(c, "text")]
    return "\n".join(texts)


async def _fetch_learner_context(session, user_id: str) -> str:
    """Fetch learner profile resource from MCP server."""
    try:
        resource = await session.read_resource(f"learner://profile/{user_id}")
        contents = [c.text for c in resource.contents if hasattr(c, "text")]
        return "\n".join(contents)
    except Exception as e:
        logger.warning(f"Could not fetch learner profile: {e}")
        return "{}"


async def _fetch_lesson_context(session, lesson_id: str) -> str:
    """Fetch lesson resource from MCP server."""
    try:
        resource = await session.read_resource(f"curriculum://lesson/{lesson_id}")
        contents = [c.text for c in resource.contents if hasattr(c, "text")]
        return "\n".join(contents)
    except Exception as e:
        logger.warning(f"Could not fetch lesson: {e}")
        return "{}"


# ════════════════════════════════════════════════════════════════════════════════
# LLM Wrappers — Each returns (text_response, tool_calls_list, provider_name)
# ════════════════════════════════════════════════════════════════════════════════

async def _call_gemini(messages: list, tools_schema: list, system_prompt: str):
    """Call Google Gemini with tool support."""
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool

    genai_client = _get_gemini_client()

    # Convert MCP tools schema to Gemini FunctionDeclarations
    gemini_tools = []
    for t in tools_schema:
        params = t.get("inputSchema", {})
        # Gemini needs properties as a dict
        gemini_tools.append(
            FunctionDeclaration(
                name=t["name"],
                description=t.get("description", ""),
                parameters={
                    "type": "object",
                    "properties": params.get("properties", {}),
                    "required": params.get("required", []),
                },
            )
        )

    model = genai_client.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt,
        tools=[Tool(function_declarations=gemini_tools)] if gemini_tools else [],
    )

    # Convert messages to Gemini format
    gemini_history = []
    last_user_msg = ""
    for m in messages:
        if m["role"] == "user":
            last_user_msg = m["content"]
        elif m["role"] == "assistant" and m.get("content"):
            gemini_history.append({"role": "model", "parts": [m["content"]]})
        elif m["role"] == "user" and gemini_history:
            gemini_history.append({"role": "user", "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history)
    response = await asyncio.to_thread(chat.send_message, last_user_msg)

    tool_calls = []
    if response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                tool_calls.append({
                    "name": fc.name,
                    "args": dict(fc.args),
                })

    text = response.text if not tool_calls else ""
    return text, tool_calls, "gemini-1.5-flash"


async def _call_deepseek(messages: list, tools_schema: list, system_prompt: str):
    """Call DeepSeek (OpenAI-compatible) with tool support."""
    client = _get_deepseek_client()

    # Build OpenAI-style tool schema
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools_schema
    ]

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    kwargs = {"model": "deepseek-chat", "messages": full_messages, "max_tokens": 1024}
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

    text = msg.content or ""
    return text, tool_calls, "deepseek-chat"


async def _call_groq(messages: list, tools_schema: list, system_prompt: str):
    """Call Groq (OpenAI-compatible) with tool support."""
    client = _get_groq_client()

    # Build OpenAI-style tool schema
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools_schema
    ]

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    # Using Llama 3.3 70b versatile for smarter context reasoning and proper tool calling
    kwargs = {"model": "llama-3.3-70b-versatile", "messages": full_messages, "max_tokens": 1024}
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

    text = msg.content or ""
    return text, tool_calls, "groq-llama3"


async def _call_ollama(messages: list, tools_schema: list, system_prompt: str):
    """Call Local Ollama (OpenAI-compatible) with tool support."""
    client = _get_ollama_client()

    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools_schema
    ]

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    model_name = config("OLLAMA_MODEL", default="llama3.1")
    kwargs = {"model": model_name, "messages": full_messages}
    if openai_tools:
        kwargs["tools"] = openai_tools

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

    text = msg.content or ""
    return text, tool_calls, f"ollama-{model_name}"


async def _call_claude(messages: list, tools_schema: list, system_prompt: str):
    """Call Anthropic Claude with tool support."""
    client = _get_claude_client()

    # Build Anthropic tool schema
    anthropic_tools = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("inputSchema", {"type": "object", "properties": {}}),
        }
        for t in tools_schema
    ]

    # Convert messages to Anthropic format (user/assistant alternating)
    anthropic_messages = []
    for m in messages:
        role = m["role"] if m["role"] in ("user", "assistant") else "user"
        content = m.get("content", "")
        if content:
            anthropic_messages.append({"role": role, "content": content})

    kwargs = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": anthropic_messages,
    }
    if anthropic_tools:
        kwargs["tools"] = anthropic_tools

    response = await client.messages.create(**kwargs)

    tool_calls = []
    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "name": block.name,
                "args": block.input,
            })

    text = "\n".join(text_parts)
    return text, tool_calls, "claude-3-5-haiku"
# ════════════════════════════════════════════════════════════════════════════════
# Race Runner
# ════════════════════════════════════════════════════════════════════════════════

async def _race_llms(messages: list, tools_schema: list, system_prompt: str):
    """
    Try DeepSeek first. If it fails, fire remaining LLMs simultaneously and 
    return the result of whichever responds first.

    Returns: (text, tool_calls, provider_name)
    """
    # 1. Try DeepSeek first as the primary LLM if configured
    if config("DEEPSEEK_API_KEY", default=""):
        try:
            return await _call_deepseek(messages, tools_schema, system_prompt)
        except Exception as e:
            logger.warning(f"DeepSeek failed, falling back to race: {e}")

    # 2. Race the remaining fallback LLMs
    providers = {}
    if config("GEMINI_API_KEY", default=""):
        providers["gemini"] = _call_gemini(messages, tools_schema, system_prompt)
    if config("ANTHROPIC_API_KEY", default=""):
        providers["claude"] = _call_claude(messages, tools_schema, system_prompt)
    if config("GROQ_API_KEY", default=""):
        providers["groq"] = _call_groq(messages, tools_schema, system_prompt)
    if config("USE_OLLAMA", default="false").lower() == "true":
        providers["ollama"] = _call_ollama(messages, tools_schema, system_prompt)

    if not providers:
        # Fallback: no API keys configured → mock response
        logger.warning("No LLM API keys configured. Returning mock response.")
        return (
            "[Mock] No LLM API keys are set. Please configure GROQ_API_KEY, "
            "GEMINI_API_KEY, DEEPSEEK_API_KEY, or ANTHROPIC_API_KEY in your .env file.",
            [],
            "mock",
        )

    tasks = [asyncio.create_task(coro, name=name) for name, coro in providers.items()]
    
    errors = []
    for coro in asyncio.as_completed(tasks):
        try:
            result = await coro
            # We got a successful response! Cancel all remaining tasks.
            for t in tasks:
                if not t.done():
                    t.cancel()
            logger.info(f"LLM race won by: {result[2]}")
            return result
        except Exception as e:
            logger.error(f"LLM task failed: {e}")
            errors.append(str(e))

    # If we get here, ALL providers failed
    return (f"All LLM providers failed: { ' | '.join(errors) }", [], "error")


# ════════════════════════════════════════════════════════════════════════════════
# Main TutorAgent Class
# ════════════════════════════════════════════════════════════════════════════════

class TutorAgent:
    """
    Orchestrates the full AI Agent loop:
      MCP server → Learner context → LLM race → Tool execution → Final response
    """

    MAX_TOOL_ROUNDS = 5  # Safety limit on agentic loop iterations

    def __init__(self):
        self.system_prompt = (
            "You are Mwalimu, an expert AI Tutor for the Uganda "
            "Competence-Based Curriculum (CBC). You are not just an answering machine; "
            "you are a highly intelligent and engaging teacher. Treat every question from a learner as a mini-lesson.\n\n"
            "Pedagogical Rules & Approach:\n"
            "1. Curriculum Focus: Only answer questions related to CBC curriculum subjects "
            "(Mathematics, Science, English, SST, ICT, etc.). If a question is out of scope (politics, violence, adult content), "
            "politely decline and redirect to curriculum topics.\n"
            "2. Contextual Learning: Teach using analogies, scenarios, and local Ugandan examples. Draw information from "
            "the learner's natural environment and surroundings so they can easily relate to the concept and see how it is applied in daily life.\n"
            "3. Natural Thinking & Problem Solving: Guide the learner to think critically. Instead of just delivering raw facts, "
            "force the learner into natural thinking by relating the problem to real-world situations they can solve.\n"
            "4. Invisible Tool Usage: Use available tools to search curriculum content for accurate, grounded answers. "
            "IMPORTANT: Never mention the names of the tools you used, your execution flow, or say 'Based on the search results...'. "
            "Just speak naturally as a human teacher would.\n"
            "5. Tone: Be encouraging, patient, tailored to the learner's class level, and pedagogically sound."
        )

    async def run_stream(
        self,
        user_id: str,
        query: str,
        context_lesson_id: Optional[str] = None,
        history: list = None,
    ):
        """
        Run the full agent loop yielding JSON strings for each step.
        """
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[MCP_SERVER_SCRIPT],
            env={**os.environ},
        )

        tool_calls_log = []

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                yield json.dumps({"type": "status", "message": "Initializing AI Tutor session..."})
                
                # ── 1. List available tools from MCP server ───────────────────
                tools_list = await session.list_tools()
                tools_schema = [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else {},
                    }
                    for t in tools_list.tools
                ]

                yield json.dumps({"type": "status", "message": "Fetching learner context..."})
                # ── 2. Build initial context ──────────────────────────────────
                learner_ctx = await _fetch_learner_context(session, user_id)
                learner_data = {}
                try:
                    learner_data = json.loads(learner_ctx)
                except json.JSONDecodeError:
                    pass

                system_prompt = self.system_prompt
                if learner_data:
                    system_prompt += (
                        f"\n\nLearner Profile:\n"
                        f"- Name: {learner_data.get('username', 'Unknown')}\n"
                        f"- Class Level: {learner_data.get('class_level', 'Unknown')}\n"
                        f"- School: {learner_data.get('school', 'Unknown')}\n"
                    )

                # ── 3. Pre-fetch lesson context if provided ───────────────────
                lesson_ctx = ""
                if context_lesson_id:
                    lesson_ctx = await _fetch_lesson_context(session, context_lesson_id)
                    try:
                        lesson_data = json.loads(lesson_ctx)
                        system_prompt += (
                            f"\n\nThe learner is currently viewing:\n"
                            f"Lesson: '{lesson_data.get('title', '')}' "
                            f"({lesson_data.get('subject', '')} — "
                            f"{lesson_data.get('class_level', '')})\n"
                            f"Competencies: "
                            f"{', '.join(c['name'] for c in lesson_data.get('competencies', []))}"
                        )
                    except (json.JSONDecodeError, TypeError):
                        pass

                # ── 4. Agentic tool-calling loop ──────────────────────────────
                messages = history or []
                messages.append({"role": "user", "content": query})

                for round_num in range(self.MAX_TOOL_ROUNDS):
                    yield json.dumps({"type": "status", "message": "Analyzing query and formulating response..."})
                    text, tool_calls, provider = await _race_llms(
                        messages, tools_schema, system_prompt
                    )

                    # No tool calls → we have a final answer
                    if not tool_calls:
                        is_out_of_scope = "out of scope" in text.lower()
                        yield json.dumps({
                            "type": "final",
                            "content": text,
                            "is_out_of_scope": is_out_of_scope,
                            "provider": provider,
                            "tool_calls_log": tool_calls_log
                        })
                        return

                    # Execute each tool call via MCP
                    tool_results = []
                    for tc in tool_calls:
                        tool_name = tc["name"]
                        tool_args = tc.get("args", {})
                        logger.info(f"Agent calling MCP tool: {tool_name}({tool_args})")
                        yield json.dumps({
                            "type": "tool_call",
                            "name": tool_name,
                            "args": tool_args
                        })

                        try:
                            result_text = await _call_mcp_tool(session, tool_name, tool_args)
                        except Exception as e:
                            result_text = json.dumps({"error": str(e)})

                        tool_calls_log.append({
                            "round": round_num + 1,
                            "tool": tool_name,
                            "args": tool_args,
                            "result_preview": result_text[:200],
                            "provider": provider,
                        })
                        tool_results.append({
                            "tool_call_id": tc.get("id", tool_name),
                            "tool_name": tool_name,
                            "result": result_text,
                        })

                    # Append assistant + tool results to conversation
                    messages.append({"role": "assistant", "content": text or "(called tools)"})
                    for tr in tool_results:
                        messages.append({
                            "role": "user",
                            "content": (
                                f"[Tool Result: {tr['tool_name']}]\n{tr['result']}"
                            ),
                        })

                # Safety fallback after MAX_TOOL_ROUNDS
                yield json.dumps({"type": "status", "message": "Finalizing answer..."})
                final_text, _, provider = await _race_llms(
                    messages + [
                        {"role": "user", "content": "Please provide your final answer now."}
                    ],
                    [],  # No tools in final round
                    system_prompt,
                )
                is_out_of_scope = "out of scope" in final_text.lower()
                yield json.dumps({
                    "type": "final",
                    "content": final_text,
                    "is_out_of_scope": is_out_of_scope,
                    "provider": provider,
                    "tool_calls_log": tool_calls_log
                })
                return


# ── Convenience sync wrapper for Django views ─────────────────────────────────
# ── Convenience sync wrapper for Django views ─────────────────────────────────
def run_tutor_agent_stream(
    user_id: str,
    query: str,
    context_lesson_id: Optional[str] = None,
    history: list = None,
):
    """
    Synchronous generator wrapper around TutorAgent.run_stream() for use in Django views.
    Runs the event loop in a background thread and yields items from a thread-safe queue.
    """
    import queue
    import threading

    q = queue.Queue()

    def run_in_thread():
        async def do_run():
            agent = TutorAgent()
            try:
                async for chunk in agent.run_stream(user_id, query, context_lesson_id, history):
                    q.put(chunk)
            except Exception as e:
                logger.exception(f"TutorAgent stream failed: {e}")
                q.put(json.dumps({
                    "type": "error",
                    "message": "I encountered an error while processing your request."
                }))
            finally:
                q.put(None)  # EOF marker
        try:
            asyncio.run(do_run())
        except Exception as e:
            q.put(json.dumps({"type": "error", "message": str(e)}))
            q.put(None)

    threading.Thread(target=run_in_thread, daemon=True).start()

    while True:
        chunk = q.get()
        if chunk is None:
            break
        yield chunk
