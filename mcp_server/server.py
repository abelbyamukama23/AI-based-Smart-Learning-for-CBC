"""
mcp_server/server.py — CBC AI Tutor MCP Server
================================================
Exposes curriculum data (lessons, competencies, learner profile, AI history)
as MCP Tools and Resources.

Transport: stdio  (run as a subprocess from the agent loop)

Usage (standalone test):
    python mcp_server/server.py
"""
import os
import sys
import json
import django

# ── Bootstrap Django so we can use ORM models ────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")
from django.apps import apps
if not apps.ready:
    django.setup()

# ── Imports (after Django setup) ──────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP
from asgiref.sync import sync_to_async

from apps.curriculum.models import Lesson, Competency, Subject, Level
from apps.curriculum.constants import (
    CURRICULUM_SEARCH_LIMIT,
    COMPETENCY_LIST_LIMIT,
    LEARNER_HISTORY_HARD_CAP,
    LIBRARY_RAG_DEFAULT_HITS,
    RAG_SEARCH_TIMEOUT_SECS,
)
from apps.accounts.models import User, Learner
from apps.ai_tutor.models import AISession
from duckduckgo_search import DDGS

# ── MCP-side RAG warm-up ──────────────────────────────────────────────────────
# The MCP server is a SEPARATE subprocess from Django — Django's AppConfig.ready()
# warm-up does NOT run here. Pre-load the model as soon as this module is imported
# so the first `search_library_rag` call does not block for 15-25 seconds.
import threading as _threading

def _mcp_warmup():
    try:
        from apps.curriculum.rag_service import warm_up_rag
        warm_up_rag()
    except Exception:
        pass  # Non-fatal: tool still works, just first call will be slower

_warmup_thread = _threading.Thread(target=_mcp_warmup, daemon=True, name="mcp-rag-warmup")
_warmup_thread.start()

# ── MCP Server Instance ───────────────────────────────────────────────────────
mcp = FastMCP(
    name="cbc-tutor-mcp",
    instructions=(
        "You are an MCP server for the CBC (Competence-Based Curriculum) "
        "Learning Platform. You provide tools to search curriculum content, "
        "fetch learner profiles, and retrieve session history so the AI Tutor "
        "can give contextually-grounded, CBC-aligned responses."
    ),
)

# ════════════════════════════════════════════════════════════════════════════════
# Sync DB helpers — pure Django ORM calls, safe to run in a thread
# ════════════════════════════════════════════════════════════════════════════════

def _db_get_learner_profile(user_id: str) -> str:
    try:
        user = User.objects.select_related("learner_profile__school").get(id=user_id)
        profile = {
            "user_id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        if hasattr(user, "learner_profile"):
            lp = user.learner_profile
            profile["class_level"] = lp.class_level
            profile["school"] = lp.school.school_name if lp.school else None
            # ── Pedagogy & Context Preferences ──────────────────────────────
            profile["preferred_methodology"] = lp.preferred_methodology  # e.g. SOCRATIC, DIRECT
            profile["preferred_language"] = lp.preferred_language        # e.g. EN, LG, SW
            profile["familiar_region"] = lp.familiar_region or None      # e.g. "Western/Ankole"
            profile["preferred_subjects"] = lp.preferred_subjects or []  # list of subject names
        return json.dumps(profile, indent=2)
    except User.DoesNotExist:
        return json.dumps({"error": f"User {user_id} not found"})


def _db_get_lesson(lesson_id: str) -> str:
    try:
        lesson = Lesson.objects.select_related("subject", "class_level").prefetch_related(
            "competencies"
        ).get(id=lesson_id)
        return json.dumps({
            "lesson_id": str(lesson.id),
            "title": lesson.title,
            "description": lesson.description,
            "subject": lesson.subject.subject_name,
            "class_level": lesson.class_level.level_name,
            "body_html": lesson.body_html,
            "video_url": lesson.video_url or "",
            "competencies": [
                {"id": str(c.id), "name": c.competency_name, "description": c.description}
                for c in lesson.competencies.all()
            ],
        }, indent=2)
    except Lesson.DoesNotExist:
        return json.dumps({"error": f"Lesson {lesson_id} not found"})


def _db_search_curriculum(subject: str, class_level: str, query: str) -> str:
    qs = Lesson.objects.select_related("subject", "class_level").filter(
        subject__is_active=True
    )
    if subject:
        qs = qs.filter(subject__subject_name__icontains=subject)
    if class_level:
        qs = qs.filter(class_level__level_name__iexact=class_level)
    if query:
        qs = qs.filter(title__icontains=query) | qs.filter(description__icontains=query)
    results = [
        {
            "lesson_id": str(l.id),
            "title": l.title,
            "subject": l.subject.subject_name,
            "class_level": l.class_level.level_name,
            "description": l.description[:300],
        }
        for l in qs[:CURRICULUM_SEARCH_LIMIT]   # ← Named constant
    ]
    return json.dumps(results, indent=2)


def _db_get_competency_list(subject: str, class_level: str) -> str:
    qs = Competency.objects.select_related("subject", "level").filter(
        subject__subject_name__icontains=subject,
        level__level_name__iexact=class_level,
    )
    results = [
        {
            "competency_id": str(c.id),
            "name": c.competency_name,
            "description": c.description,
            "subject": c.subject.subject_name,
            "class_level": c.level.level_name,
        }
        for c in qs[:COMPETENCY_LIST_LIMIT]   # ← Named constant
    ]
    return json.dumps(results, indent=2)


def _db_get_learner_history(user_id: str, limit: int) -> str:
    limit = min(limit, LEARNER_HISTORY_HARD_CAP)   # ← Named constant
    sessions = AISession.objects.filter(learner__id=user_id).order_by("-timestamp")[:limit]
    results = [
        {
            "session_id": str(s.id),
            "query": s.query,
            "response": s.response[:500] if s.response else "",
            "flagged_out_of_scope": s.flagged_out_of_scope,
            "timestamp": s.timestamp.isoformat(),
        }
        for s in sessions
    ]
    return json.dumps(results, indent=2)


def _db_get_available_subjects() -> str:
    subjects = Subject.objects.filter(is_active=True).values("id", "subject_name")
    return json.dumps(
        [{"subject_id": str(s["id"]), "name": s["subject_name"]} for s in subjects],
        indent=2,
    )


# ════════════════════════════════════════════════════════════════════════════════
# RESOURCES — Read-only data the LLM can fetch
# All handlers are async and use sync_to_async to avoid Django ORM/async conflict
# ════════════════════════════════════════════════════════════════════════════════

@mcp.resource("learner://profile/{user_id}")
async def get_learner_profile_resource(user_id: str) -> str:
    """
    Fetch a learner's profile: name, email, class level, school, role.
    Returns JSON string.
    """
    return await sync_to_async(_db_get_learner_profile)(user_id)


@mcp.resource("curriculum://lesson/{lesson_id}")
async def get_lesson_resource(lesson_id: str) -> str:
    """
    Fetch a lesson's full content by ID.
    Returns JSON string with title, subject, class_level, body_html, competencies.
    """
    return await sync_to_async(_db_get_lesson)(lesson_id)


# ════════════════════════════════════════════════════════════════════════════════
# TOOLS — Functions the LLM can call to retrieve or act on data
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_curriculum(subject: str = "", class_level: str = "", query: str = "") -> str:
    """
    Search CBC lessons and competencies by subject, class level, and/or keyword.

    Args:
        subject:     Subject name filter (e.g. 'Mathematics', 'Biology'). Optional.
        class_level: Class level filter (e.g. 'S1', 'S3'). Optional.
        query:       Keyword to search in lesson titles and descriptions. Optional.

    Returns:
        JSON list of matching lessons (id, title, subject, class_level, description).
    """
    return await sync_to_async(_db_search_curriculum)(subject, class_level, query)


@mcp.tool()
async def get_lesson_content(lesson_id: str) -> str:
    """
    Fetch the full body content of a specific lesson by its UUID.

    Args:
        lesson_id: UUID of the lesson.

    Returns:
        JSON object with title, subject, class_level, body_html, video_url, competencies.
    """
    return await sync_to_async(_db_get_lesson)(lesson_id)


@mcp.tool()
async def get_competency_list(subject: str, class_level: str) -> str:
    """
    List all official CBC competencies for a given subject and class level.

    Args:
        subject:     Subject name (e.g. 'Chemistry').
        class_level: Class level (e.g. 'S2').

    Returns:
        JSON list of competencies (id, name, description).
    """
    return await sync_to_async(_db_get_competency_list)(subject, class_level)


@mcp.tool()
async def get_learner_history(user_id: str, limit: int = 5) -> str:
    """
    Retrieve the most recent AI Tutor session history for a learner.

    Args:
        user_id: UUID of the learner's user account.
        limit:   Number of past sessions to return (default 5, max 10).

    Returns:
        JSON list of recent sessions (query, response, timestamp, flagged).
    """
    return await sync_to_async(_db_get_learner_history)(user_id, limit)


@mcp.tool()
async def get_available_subjects() -> str:
    """
    List all active CBC subjects available on the platform.

    Returns:
        JSON list of subjects (id, name).
    """
    return await sync_to_async(_db_get_available_subjects)()


@mcp.tool()
async def search_uganda_curriculum_web(query: str) -> str:
    """
    Search the web for Uganda Competence Based Curriculum (CBC) topics.
    Use this tool when the local database does not have enough information.
    
    Args:
        query: The topic to search for (e.g. 'Photosynthesis', 'World War 2').
        
    Returns:
        JSON string containing the top web search results.
    """
    def _do_search():
        try:
            full_query = f"Uganda Competence Based Curriculum CBC {query}"
            results = DDGS().text(full_query, max_results=3)
            return json.dumps(list(results), indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
            
    return await sync_to_async(_do_search)()

@mcp.tool()
async def research_youtube_video(query: str) -> str:
    """
    Search YouTube for educational videos and return their transcribed text content.
    Use this to gather deep, rich context from videos. 
    DO NOT return the YouTube URLs or video IDs to the user. Instead, read the transcript 
    returned by this tool and synthesize the information into your own lesson.
    
    Args:
        query: The educational topic to search for on YouTube.
        
    Returns:
        JSON string containing the video title, description, and full text transcript.
    """
    def _do_youtube_research():
        try:
            from youtubesearchpython import VideosSearch
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # 1. Search for the top video
            videos_search = VideosSearch(query, limit=1)
            result = videos_search.result()
            
            if not result or not result.get("result"):
                return json.dumps({"error": "No YouTube videos found for this topic."})
                
            video = result["result"][0]
            video_id = video["id"]
            title = video.get("title", "Unknown Title")
            
            # 2. Fetch the transcript
            try:
                # Try to get English transcript first, fallback to auto-generated
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                try:
                    transcript = transcript_list.find_transcript(['en'])
                except:
                    # If no manual English transcript, grab the first available generated one
                    transcript = transcript_list.filter(is_generated=True)[0]
                
                transcript_data = transcript.fetch()
                # Combine text
                full_text = " ".join([t["text"] for t in transcript_data])
                
                # Limit text to ~2000 words (approx 12000 chars) to avoid blowing up context window
                if len(full_text) > 12000:
                    full_text = full_text[:12000] + "... (transcript truncated)"
                    
                return json.dumps({
                    "title": title,
                    "transcript": full_text,
                    "note": "Synthesize this information into your lesson. DO NOT share the video link with the user."
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "error": f"Found video '{title}' but could not extract transcript. Error: {str(e)}"
                })
                
        except Exception as e:
            return json.dumps({"error": str(e)})
            
    return await sync_to_async(_do_youtube_research)()


# ════════════════════════════════════════════════════════════════════════════════
# Library Agent Tools — RAG-powered curriculum knowledge base
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_library_rag(
    query: str,
    subject: str = "",
    class_level: str = "",
) -> str:
    """
    PRIMARY SEARCH TOOL — Search the curriculum library using semantic similarity (RAG).
    Always try this tool FIRST before searching the web.
    Returns textbook excerpts, lesson summaries, maps, and teaching materials
    that are directly sourced from the Uganda CBC curriculum database.

    Args:
        query: The learning topic or question (e.g. 'How does photosynthesis work?').
        subject: Optional subject filter (e.g. 'Biology', 'Mathematics').
        class_level: Optional class level filter (e.g. 'S1', 'S2', 'P6').

    Returns:
        JSON string with ranked library materials most relevant to the query.
    """
    import logging
    _log = logging.getLogger(__name__)

    def _do_rag_search():
        import concurrent.futures

        def _search_with_timeout():
            try:
                from apps.curriculum.rag_service import search_library
                from apps.curriculum.exceptions import RAGServiceError

                try:
                    results = search_library(
                        query, subject=subject, class_level=class_level,
                        n_results=LIBRARY_RAG_DEFAULT_HITS,  # ← Named constant
                    )
                except RAGServiceError as e:
                    # Circuit Breaker — log and fall through to keyword fallback
                    _log.warning("RAG service unavailable: %s — using keyword fallback", e)
                    results = []

                if results:
                    return json.dumps({
                        "source": "curriculum_library",
                        "count": len(results),
                        "results": results,
                    }, indent=2)

                # Fallback: keyword search in DB if vector store is empty
                from apps.curriculum.models import Lesson
                lessons = Lesson.objects.filter(
                    title__icontains=query
                ).select_related("subject", "class_level")[:3]

                if lessons:
                    db_results = [
                        {
                            "title": l.title,
                            "subject": l.subject.subject_name if l.subject else "",
                            "class_level": l.class_level.level_name if l.class_level else "",
                            "excerpt": (l.description or l.body_html or "")[:400],
                            "type": "lesson",
                            "relevance": 0.6,
                        }
                        for l in lessons
                    ]
                    return json.dumps({
                        "source": "curriculum_db_keyword",
                        "count": len(db_results),
                        "results": db_results,
                    }, indent=2)

                return json.dumps({"source": "curriculum_library", "count": 0, "results": []})

            except Exception as e:
                return json.dumps({"error": str(e)})

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_search_with_timeout)
                return future.result(timeout=RAG_SEARCH_TIMEOUT_SECS)  # ← Named constant
        except concurrent.futures.TimeoutError:
            return json.dumps({
                "source": "curriculum_library",
                "count": 0,
                "results": [],
                "note": "Library index is warming up. Falling back to web search.",
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    return await sync_to_async(_do_rag_search)()

@mcp.tool()
async def compile_lesson_from_material(

    material_title: str,
    topic: str,
) -> str:
    """
    Library Agent: compile a structured lesson from a specific curriculum material.
    Searches the library for the material and returns a structured compilation with:
    key lessons, real-world application (Uganda context), main message, and challenge questions.

    Args:
        material_title: Title or keyword of the book/file to read from.
        topic: The specific topic within the material to focus on.

    Returns:
        JSON string with structured lesson components ready to teach to the learner.
    """
    def _do_compile():
        try:
            from apps.curriculum.rag_service import search_library, compile_lesson

            # Search for the specific material
            results = search_library(f"{material_title} {topic}", n_results=3)
            if not results:
                return json.dumps({
                    "error": f"No material found for '{material_title}' on topic '{topic}'. "
                             "The library may need more content — try search_library_rag or web_search_curriculum."
                })

            excerpts = [r["excerpt"] for r in results]
            source   = results[0]["title"]
            lesson   = compile_lesson(source, topic, excerpts)

            return json.dumps({
                "source_material": lesson["source_material"],
                "topic":           lesson["topic"],
                "context":         lesson["context"],
                "compile_prompt":  lesson["instruction"],
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    return await sync_to_async(_do_compile)()


@mcp.tool()
async def research_and_save_curriculum(
    topic: str,
    subject: str = "",
    class_level: str = "",
) -> str:
    """
    Research Agent: Automatically discover, score, and save relevant curriculum
    content from the web when the library has no results for a topic.

    Use this tool ONLY when search_library_rag returns 0 results.
    The agent will:
      1. Search the web for Uganda CBC resources on this topic
      2. Score each source for curriculum relevance (0.0-1.0)
      3. Auto-save high-confidence content (>0.80) directly to the library
      4. Queue borderline content (0.50-0.80) for admin review at /admin/

    Args:
        topic: The curriculum topic to research (e.g. 'Photosynthesis', 'Fractions').
        subject: Subject name to filter results (e.g. 'Biology', 'Mathematics').
        class_level: Target class level (e.g. 'S1', 'P6').

    Returns:
        JSON summary of discovered and saved content.
    """
    def _do_research():
        try:
            from apps.curriculum.research_agent import research_and_save
            result = research_and_save(
                topic=topic,
                subject=subject,
                class_level=class_level,
                max_sources=3,
            )
            summary = {
                "sources_checked":  result["sources_checked"],
                "auto_approved":    len(result["auto_approved"]),
                "pending_review":   len(result["pending_review"]),
                "discarded":        result["discarded"],
                "new_library_items": [
                    {"title": i["title"], "score": i["score"]}
                    for i in result["auto_approved"]
                ],
            }
            if result["auto_approved"]:
                summary["message"] = (
                    f"Added {len(result['auto_approved'])} new resource(s) to the library. "
                    f"Now retry search_library_rag to get the content."
                )
            elif result["pending_review"]:
                summary["message"] = (
                    f"Found {len(result['pending_review'])} resource(s) that need admin review "
                    f"at /admin/ before they appear in the library."
                )
            else:
                summary["message"] = "No sufficiently relevant resources found online for this topic."
            return json.dumps(summary, indent=2)
        except Exception as e:
            import logging
            logging.error(f"Background research error: {e}")
            return json.dumps({"error": str(e)})

    import asyncio
    
    # Dispatch as a background task to prevent blocking the agent stream
    asyncio.create_task(sync_to_async(_do_research)())
    
    return json.dumps({
        "status": "Job queued",
        "message": "The research task has been dispatched to the background. Proceed with teaching the learner, and inform them that the resources will be available in the library shortly."
    })


# ════════════════════════════════════════════════════════════════════════════════
# Expert Tools — Math and Knowledge Graph
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def calculate_math_expression(expression: str) -> str:
    """
    Math Expert Tool: Safely evaluate a mathematical expression using Python's math module.
    Use this to verify any calculations before presenting them to the learner.

    Args:
        expression: The mathematical expression to evaluate (e.g., "5 * (3 + 2)", "math.sqrt(16)").

    Returns:
        JSON string containing the calculated result or an error message.
    """
    def _do_calculate():
        import sympy
        try:
            # Parse the mathematical expression securely using sympy (prevents code execution attacks)
            expr = sympy.sympify(expression)
            # Evaluate it to a float, but also return the exact mathematical string
            result = float(expr.evalf())
            return json.dumps({"expression": expression, "result": result, "exact": str(expr)})
        except Exception as e:
            return json.dumps({"error": f"Failed to calculate expression safely: {str(e)}"})

    return await sync_to_async(_do_calculate)()


@mcp.tool()
async def query_knowledge_graph(topic: str, query_type: str = "prerequisites") -> str:
    """
    Expert Agent Tool: Traverse the Curriculum Knowledge Graph to understand learning paths.

    Args:
        topic: The conceptual topic to query (e.g., 'Algebra', 'Photosynthesis').
        query_type: The type of traversal to run. Allowed values: 'prerequisites' (finds what to learn before).

    Returns:
        JSON string containing the related graph nodes.
    """
    def _do_query():
        try:
            from apps.ai_tutor.knowledge_graph import KnowledgeGraphService
            kg = KnowledgeGraphService()
            
            if query_type == "prerequisites":
                prereqs = kg.get_prerequisites(topic)
                # If topic doesn't match ID, we do a name search
                if not prereqs:
                    kg.load_graph()
                    node_id = next((n for n, d in kg._graph.nodes(data=True) if d.get('name', '').lower() == topic.lower()), None)
                    if node_id:
                        prereqs = kg.get_prerequisites(node_id)
                
                return json.dumps({
                    "topic": topic,
                    "query_type": "prerequisites",
                    "results": prereqs
                }, indent=2)
            else:
                return json.dumps({"error": "Unknown query_type. Use 'prerequisites'."})
        except Exception as e:
            return json.dumps({"error": str(e)})

    return await sync_to_async(_do_query)()

@mcp.tool()
async def taxonomy_lookup(species_name: str) -> str:
    """
    Biology Expert Tool: Look up the taxonomy and basic traits of a species.
    
    Args:
        species_name: The common or scientific name of the organism.
    """
    def _do_lookup():
        import urllib.request
        import json
        try:
            # Using Wikipedia API for a quick taxonomic lookup
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(species_name)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'MwalimuAI/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())
                return json.dumps({
                    "species": species_name,
                    "summary": data.get("extract", "No data found."),
                    "source": "Wikipedia"
                })
        except Exception as e:
            return json.dumps({"error": f"Taxonomy lookup failed: {str(e)}"})
            
    return await sync_to_async(_do_lookup)()

@mcp.tool()
async def generate_biological_diagram(anatomy_part: str) -> str:
    """
    Biology Expert Tool: Generate an SVG diagram for biological anatomy or cells.
    
    Args:
        anatomy_part: The biological structure to draw (e.g. 'plant cell', 'heart').
    """
    def _do_draw():
        # In a production environment, this would call a specialized diagram generation API
        # or fetch pre-made SVGs from the curriculum database.
        # For now, we return a structured placeholder that the frontend could render.
        return json.dumps({
            "type": "diagram",
            "subject": anatomy_part,
            "status": "Diagram generation requested. (Note: Visuals are rendered on the frontend dashboard).",
            "labels_to_teach": ["Nucleus", "Mitochondria", "Cell Membrane"] if "cell" in anatomy_part.lower() else ["Component 1", "Component 2"]
        })
        
    return await sync_to_async(_do_draw)()


# ════════════════════════════════════════════════════════════════════════════════
# Entry point — stdio transport
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    mcp.run(transport="stdio")
