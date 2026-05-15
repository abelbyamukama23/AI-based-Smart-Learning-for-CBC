"""
apps/ai_tutor/agent.py — TutorAgent (Refactored for Multi-Agent Architecture)
==============================================================================
Design Patterns applied:
  • Strategy Pattern  — LLM providers are injected via LLMRace.
  • Factory Pattern   — AgentRouter instantiates specialized agents based on mode.
  • Base Class (DRY)  — BaseTutorAgent holds the common streaming/tool loops.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_THIS_FILE   = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_FILE)))
MCP_SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "mcp_server", "server.py")

# ════════════════════════════════════════════════════════════════════════════════
# MCP Tool Execution Helpers
# ════════════════════════════════════════════════════════════════════════════════

async def _call_mcp_tool(tool_name: str, tool_args: dict) -> str:
    from mcp_server.server import mcp
    try:
        result = await mcp.call_tool(tool_name, tool_args)
        if isinstance(result, tuple) and result:
            texts = [c.text for c in result[0] if hasattr(c, "text")]
            return "\n".join(texts)
        return str(result)
    except Exception as e:
        logger.warning("Error calling MCP tool %s: %s", tool_name, e)
        return json.dumps({"error": str(e)})


async def _fetch_learner_context(user_id: str) -> str:
    from asgiref.sync import sync_to_async
    from mcp_server.server import _db_get_learner_profile
    try:
        return await sync_to_async(_db_get_learner_profile)(user_id)
    except Exception as e:
        logger.warning("Could not fetch learner profile: %s", e)
        return "{}"


async def _fetch_lesson_context(lesson_id: str) -> str:
    from asgiref.sync import sync_to_async
    from mcp_server.server import _db_get_lesson
    try:
        return await sync_to_async(_db_get_lesson)(lesson_id)
    except Exception as e:
        logger.warning("Could not fetch lesson: %s", e)
        return "{}"

# ════════════════════════════════════════════════════════════════════════════════
# System Prompts
# ════════════════════════════════════════════════════════════════════════════════

_PLANNING_PROMPT = (
    "\nBefore responding, you MUST silently plan your approach. Think step-by-step:\n"
    "1. Identify the core concept the learner is asking about.\n"
    "2. Determine what local Ugandan example or context will make this concept relatable.\n"
    "3. Decide if a visual aid (SVG diagram or infographic) is needed to simulate or explain the concept.\n"
    "4. Decide if you need to use the `research_youtube_video` tool to gather deeper knowledge from video transcripts.\n"
)

_FORMATTING_PROMPT = (
    "\nFormatting Rules:\n"
    "- KEY CONCEPTS: Always wrap key concepts, vocabulary, or important terms in **double asterisks** so they render as highlighted bold text for the learner.\n"
    "- MATH/EQUATIONS: Always format mathematical equations using LaTeX. For inline math, use `$inline$`. For block equations, you MUST put `$$` on their own separate lines before and after the equation. NEVER put other text on the same line as `$$` or the formatting will break.\n"
    "- LATEX ESCAPING: You MUST escape percent signs as `\\%` inside math blocks, otherwise it acts as a comment and breaks the entire equation renderer.\n"
    "- VISUALS & SIMULATIONS: If a diagram, simulation, or infographic is helpful, generate it using inline SVG code blocks. Format it exactly like this: ````svg <svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"...\">...</svg> ````. Make sure the SVG is responsive.\n"
    "- SVG STYLING: Our UI is in Dark Mode. You MUST use white or very light colors (like #ffffff, #e5e7eb, #9ca3af) for all SVG strokes and text fills. NEVER use black or dark colors, as they will be completely invisible.\n"
    "- INTERACTIVE SVGS: You MUST make your SVGs interactive. Add a `data-annotation=\"description here\"` attribute to key SVG elements (like <path>, <circle>, <g>, or <rect>). The frontend will use this to show a tooltip explaining that specific part when the learner hovers over it. Example: `<circle data-annotation=\"The Nucleus: Contains DNA\" ... />`.\n"
    "- NO EXTERNAL LINKS: NEVER provide raw YouTube links or URLs to the user. Keep all learning within the chat. If you use a tool to research a video, read the transcript and synthesize the lesson yourself.\n"
)

_DEFAULT_SYSTEM_PROMPT = (
    "You are Mwalimu, an expert AI Tutor for the Uganda Competence-Based Curriculum (CBC).\n"
    "Pedagogical Rules & Approach:\n"
    "1. Curriculum Focus: Only answer questions related to CBC curriculum subjects.\n"
    "2. Contextual Learning: Teach using local Ugandan examples. Relate concepts to everyday life.\n"
    "3. ASSIGNMENT ETHICS: If asked to solve homework, do NOT give the answer. Guide step-by-step.\n"
    "4. INVISIBLE EXECUTION: Never say 'Let me search' or 'Based on my search'. Just TEACH.\n"
    "5. Use tools like `search_library_rag` or `research_youtube_video` silently to build your knowledge before answering.\n"
    + _PLANNING_PROMPT + _FORMATTING_PROMPT
)

_MATH_EXPERT_PROMPT = (
    "You are Mwalimu's Math Expert Agent for the Uganda CBC.\n"
    "Pedagogical Focus:\n"
    "- You use Socratic questioning to guide learners through step-by-step mathematical problem solving.\n"
    "- You NEVER give the final answer immediately.\n"
    "- You verify math calculations using your 'calculate_math_expression' tool to avoid hallucinations.\n"
    "- Use 'query_knowledge_graph' to understand prerequisites before teaching advanced topics.\n"
    "- INVISIBLE EXECUTION: Never state 'Let me calculate' or 'Let me search'. Just respond.\n"
    + _PLANNING_PROMPT + _FORMATTING_PROMPT
)

_BIOLOGY_EXPERT_PROMPT = (
    "You are Mwalimu's Biology Expert Agent for the Uganda CBC.\n"
    "Pedagogical Focus:\n"
    "- You focus on observational analysis, cellular biology, anatomy, and ecology.\n"
    "- You relate biological concepts to the human body and local Ugandan flora/fauna.\n"
    "- Use your specialized tools like 'generate_biological_diagram' or 'taxonomy_lookup' to enhance learning.\n"
    "- Extremely Important: You must use ````svg ```` blocks to visually illustrate biology concepts whenever possible.\n"
    "- Use 'query_knowledge_graph' to understand prerequisites before teaching advanced topics.\n"
    "- INVISIBLE EXECUTION: Never state 'Let me generate' or 'Let me search'. Just respond naturally.\n"
    + _PLANNING_PROMPT + _FORMATTING_PROMPT
)

_PROFESSOR_EXPERT_PROMPT = (
    "You are Mwalimu's Professor Agent for the Uganda CBC.\n"
    "Pedagogical Focus:\n"
    "- You are the highest level of academic authority. Your goal is to synthesize knowledge across multiple subjects.\n"
    "- You challenge learners with advanced critical thinking questions, real-world application, and academic rigor.\n"
    "- You have access to ALL specialized tools across all subjects.\n"
    "- Use 'query_knowledge_graph' extensively to build cross-disciplinary learning paths.\n"
    "- INVISIBLE EXECUTION: Never state 'Let me search' or 'I will use a tool'. Just teach.\n"
    + _PLANNING_PROMPT + _FORMATTING_PROMPT
)

_INTERNAL_PREFIXES = (
    "let me ", "let me also", "let me now", "alright!", "alright,",
    "based on my search", "based on the search", "based on the results",
    "according to the system", "the platform shows", "the system shows",
    "i found that", "i'll now", "i will now", "now let me",
    "let me look", "let me check", "let me find",
    "let me search", "let me retrieve", "let me fetch",
)

def _clean_response(text: str) -> str:
    if not text:
        return text
    kept = [
        line for line in text.splitlines()
        if not any(line.strip().lower().startswith(p) for p in _INTERNAL_PREFIXES)
    ]
    result, blanks = [], 0
    for line in kept:
        if line.strip() == "":
            blanks += 1
            if blanks <= 1:
                result.append(line)
        else:
            blanks = 0
            result.append(line)
    return "\n".join(result).strip()

# ════════════════════════════════════════════════════════════════════════════════
# Base Agent Class
# ════════════════════════════════════════════════════════════════════════════════

class BaseTutorAgent:
    MAX_TOOL_ROUNDS = 5

    def __init__(self):
        from .llm import (
            ClaudeProvider, DeepSeekProvider, GeminiProvider,
            GroqProvider, LLMRace, OllamaProvider,
        )
        self._race = LLMRace([
            DeepSeekProvider(),
            GeminiProvider(),
            ClaudeProvider(),
            GroqProvider(),
            OllamaProvider(),
        ])

    def get_system_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement this.")

    def get_allowed_tools(self, all_tools: List[Dict]) -> List[Dict]:
        return all_tools  # Allow all by default

    async def _classify_intent(self, query: str) -> str:
        classifier_prompt = (
            "You are an intent classifier for an educational AI Tutor.\n"
            "Classify the user's latest message into one of three categories:\n"
            "1. CHAT: Greetings, off-topic, or non-educational questions.\n"
            "2. READ_MATERIAL: User asks to read a book, lesson, or curriculum material.\n"
            "3. QUESTION: Educational or curriculum-based conceptual question.\n"
            "Return ONLY the category name. No other text."
        )
        try:
            text, _, _ = await self._race.run([{"role": "user", "content": query}], [], classifier_prompt)
            clean = text.strip().upper()
            if "CHAT" in clean: return "CHAT"
            if "READ_MATERIAL" in clean: return "READ_MATERIAL"
            return "QUESTION"
        except Exception:
            return "QUESTION"

    async def run_stream(
        self,
        user_id: str,
        query: str,
        context_lesson_id: Optional[str] = None,
        history: list = None,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ):
        tool_calls_log = []

        yield json.dumps({"type": "status", "message": "Classifying your request..."})
        intent = await self._classify_intent(query)
        logger.info("Intent classified: %s", intent)

        # Build prompt
        yield json.dumps({"type": "status", "message": "Fetching learner context..."})
        learner_ctx = await _fetch_learner_context(user_id)
        system_prompt = self.get_system_prompt()
        
        try:
            learner_data = json.loads(learner_ctx)
            if learner_data:
                learner_name = learner_data.get('first_name') or learner_data.get('username') or 'Learner'
                system_prompt += (
                    f"\n\nLearner Profile:\n"
                    f"- Name: {learner_name}\n"
                    f"- Class Level: {learner_data.get('class_level', 'Unknown')}\n"
                    f"- School: {learner_data.get('school', 'Unknown')}\n"
                )

                # ── Dynamic Pedagogy Injection ──────────────────────────────
                methodology = learner_data.get('preferred_methodology', 'SOCRATIC')
                language = learner_data.get('preferred_language', 'EN')
                region = learner_data.get('familiar_region')

                METHODOLOGY_DIRECTIVES = {
                    'SOCRATIC': "Use the Socratic method: guide the learner with probing questions instead of giving direct answers. Help them discover the concept themselves.",
                    'DIRECT': "Use direct instruction: give clear, concise, step-by-step explanations. Get to the point efficiently without excessive questioning.",
                    'VISUAL': "Use Visual & Storytelling: frame every concept inside a relatable story or vivid analogy. Build mental imagery. Draw diagrams proactively.",
                    'PROJECT': "Use a Project-Based approach: anchor every explanation in a real-world practical task or problem the learner could actually carry out.",
                }
                LANGUAGE_NAMES = {
                    'EN': 'English', 'LG': 'Luganda', 'SW': 'Swahili', 'RN': 'Runyankole',
                }

                system_prompt += "\n\nADAPTIVE PEDAGOGY DIRECTIVES (HIGHEST PRIORITY):\n"
                system_prompt += f"- METHODOLOGY: {METHODOLOGY_DIRECTIVES.get(methodology, METHODOLOGY_DIRECTIVES['SOCRATIC'])}\n"
                if language != 'EN':
                    lang_name = LANGUAGE_NAMES.get(language, language)
                    system_prompt += f"- LANGUAGE: When the learner asks for a translation or seems confused, translate the key explanation into {lang_name}. Default output remains English.\n"
                if region:
                    system_prompt += f"- REGIONAL CONTEXT: The learner is from the {region} region of Uganda. ALWAYS use examples, names, places, economic activities, and cultural references specific to {region} as your FIRST CHOICE when explaining any concept before considering other contexts.\n"

        except json.JSONDecodeError:
            pass

        if context_lesson_id:
            lesson_ctx = await _fetch_lesson_context(context_lesson_id)
            try:
                lesson_data = json.loads(lesson_ctx)
                system_prompt += (
                    f"\n\nThe learner is currently viewing:\n"
                    f"Lesson: '{lesson_data.get('title', '')}' "
                    f"({lesson_data.get('subject', '')} — {lesson_data.get('class_level', '')})\n"
                    f"Competencies: {', '.join(c['name'] for c in lesson_data.get('competencies', []))}"
                )
            except (json.JSONDecodeError, TypeError):
                pass

        messages = list(history or [])
        messages.append({"role": "user", "content": query})

        if intent == "CHAT":
            yield json.dumps({"type": "status", "message": "Formulating response..."})
            text_buffer = ""
            provider = "deepseek"
            
            async for item in self._race.stream_run(
                messages, [], system_prompt, image_b64=image_b64, image_mime=image_mime
            ):
                if item["type"] == "chunk":
                    text_buffer += item["content"]
                    yield json.dumps(item)
            
            clean = _clean_response(text_buffer)
            yield json.dumps({
                "type": "final",
                "content": clean,
                "is_out_of_scope": "out of scope" in clean.lower(),
                "provider": provider,
                "tool_calls_log": [],
            })
            return

        from mcp_server.server import mcp
        raw_tools = await mcp.list_tools()
        tools_schema = self.get_allowed_tools([
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else {},
            }
            for t in raw_tools
        ])

        failed_tools = {}

        for round_num in range(self.MAX_TOOL_ROUNDS):
            yield json.dumps({"type": "status", "message": "Analyzing query and formulating response..."})
            round_img   = image_b64  if round_num == 0 else None
            round_mime  = image_mime if round_num == 0 else None

            text_buffer = ""
            tool_calls = []
            provider = "deepseek"

            async for item in self._race.stream_run(
                messages, tools_schema, system_prompt,
                image_b64=round_img, image_mime=round_mime,
            ):
                if item["type"] == "chunk":
                    text_buffer += item["content"]
                    yield json.dumps(item)
                elif item["type"] == "tool_calls":
                    tool_calls = item["tool_calls"]

            if not tool_calls:
                clean = _clean_response(text_buffer)
                yield json.dumps({
                    "type": "final",
                    "content": clean,
                    "is_out_of_scope": "out of scope" in clean.lower(),
                    "provider": provider,
                    "tool_calls_log": tool_calls_log,
                })
                return

            tool_results = []
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                yield json.dumps({"type": "tool_call", "name": tool_name, "args": tool_args})

                result_text = await _call_mcp_tool(tool_name, tool_args)
                
                # Circuit Breaker Pattern
                if "Error" in str(result_text):
                    failed_tools[tool_name] = failed_tools.get(tool_name, 0) + 1
                    if failed_tools[tool_name] >= 2:
                        logger.warning("Circuit breaker tripped for tool: %s", tool_name)
                        result_text += "\n[SYSTEM ALERT]: This tool has failed 2 times. DO NOT call it again. Proceed without it."
                else:
                    failed_tools[tool_name] = 0

                tool_calls_log.append({
                    "round": round_num + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result_preview": result_text[:200],
                    "provider": provider,
                })
                tool_results.append({
                    "tool_call_id": tc["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": result_text,
                })

            formatted_tool_calls = []
            for tc in tool_calls:
                formatted_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("args", {}))
                    }
                })

            messages.append({"role": "assistant", "content": text_buffer, "tool_calls": formatted_tool_calls})
            messages.extend(tool_results)

        yield json.dumps({"type": "status", "message": "Finalizing answer..."})
        
        final_text_buffer = ""
        provider = "deepseek"
        
        async for item in self._race.stream_run(
            messages + [{"role": "user", "content": "Please provide your final answer now. Speak directly to the learner."}],
            [],
            system_prompt
        ):
            if item["type"] == "chunk":
                final_text_buffer += item["content"]
                yield json.dumps(item)

        clean_final = _clean_response(final_text_buffer)
        yield json.dumps({
            "type": "final",
            "content": clean_final,
            "is_out_of_scope": "out of scope" in clean_final.lower(),
            "provider": provider,
            "tool_calls_log": tool_calls_log,
        })

# ════════════════════════════════════════════════════════════════════════════════
# Specialized Agents
# ════════════════════════════════════════════════════════════════════════════════

class DefaultTutorAgent(BaseTutorAgent):
    def get_system_prompt(self) -> str:
        return _DEFAULT_SYSTEM_PROMPT


class MathExpertAgent(BaseTutorAgent):
    def get_system_prompt(self) -> str:
        return _MATH_EXPERT_PROMPT
        
    def get_allowed_tools(self, all_tools: List[Dict]) -> List[Dict]:
        math_tools = ["search_library_rag", "query_knowledge_graph", "calculate_math_expression", "web_search_curriculum"]
        return [t for t in all_tools if t["name"] in math_tools]


class BiologyExpertAgent(BaseTutorAgent):
    def get_system_prompt(self) -> str:
        return _BIOLOGY_EXPERT_PROMPT
        
    def get_allowed_tools(self, all_tools: List[Dict]) -> List[Dict]:
        bio_tools = ["search_library_rag", "query_knowledge_graph", "taxonomy_lookup", "generate_biological_diagram", "web_search_curriculum"]
        return [t for t in all_tools if t["name"] in bio_tools]


class ProfessorAgent(BaseTutorAgent):
    def get_system_prompt(self) -> str:
        return _PROFESSOR_EXPERT_PROMPT
    
    # The Professor gets ALL tools by default.


# ════════════════════════════════════════════════════════════════════════════════
# Agent Router & Factory
# ════════════════════════════════════════════════════════════════════════════════

class AgentRouter:
    _instances = {}

    @classmethod
    def get_agent(cls, mode: str, query: str = "") -> BaseTutorAgent:
        agent_class = DefaultTutorAgent

        if mode == "expert":
            # Simple heuristic routing to the right expert
            q = query.lower()
            if any(w in q for w in ["math", "equation", "solve", "calculate", "algebra", "geometry", "+", "-", "*", "/"]):
                agent_class = MathExpertAgent
            elif any(w in q for w in ["biology", "cell", "plant", "animal", "anatomy", "photosynthesis", "organ", "reproduction"]):
                agent_class = BiologyExpertAgent
        elif mode == "professor":
            agent_class = ProfessorAgent

        if agent_class not in cls._instances:
            cls._instances[agent_class] = agent_class()
            
        return cls._instances[agent_class]


def get_agent(mode: str = "default", query: str = "") -> BaseTutorAgent:
    return AgentRouter.get_agent(mode, query)


# ════════════════════════════════════════════════════════════════════════════════
# Sync wrapper for Django views
# ════════════════════════════════════════════════════════════════════════════════

def run_tutor_agent_stream(
    user_id: str,
    query: str,
    context_lesson_id: Optional[str] = None,
    history: list = None,
    image_b64: Optional[str] = None,
    image_mime: Optional[str] = None,
    mode: str = "default",
):
    import queue
    import threading

    q: queue.Queue = queue.Queue()
    agent = get_agent(mode, query)

    def run_in_thread():
        async def do_run():
            try:
                async for chunk in agent.run_stream(
                    user_id, query, context_lesson_id, history, image_b64, image_mime
                ):
                    q.put(chunk)
            except Exception as exc:
                logger.exception("Agent stream failed: %s", exc)
                q.put(json.dumps({"type": "error", "message": str(exc)}))
            finally:
                q.put(None)

        try:
            asyncio.run(do_run())
        except Exception as exc:
            q.put(json.dumps({"type": "error", "message": str(exc)}))
            q.put(None)

    threading.Thread(target=run_in_thread, daemon=True).start()

    while True:
        chunk = q.get()
        if chunk is None:
            break
        yield chunk
