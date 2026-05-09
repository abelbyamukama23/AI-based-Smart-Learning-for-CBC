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
# Add project root to sys.path so `apps.*` imports resolve
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbc_backend.settings")
django.setup()

# ── Imports (after Django setup) ──────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP
from asgiref.sync import sync_to_async

from apps.curriculum.models import Lesson, Competency, Subject, Level
from apps.accounts.models import User, Learner
from apps.ai_tutor.models import AISession
from duckduckgo_search import DDGS

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
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        if hasattr(user, "learner_profile"):
            lp = user.learner_profile
            profile["class_level"] = lp.class_level
            profile["school"] = lp.school.school_name if lp.school else None
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
        for l in qs[:10]
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
        for c in qs[:20]
    ]
    return json.dumps(results, indent=2)


def _db_get_learner_history(user_id: str, limit: int) -> str:
    limit = min(limit, 10)
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


# ════════════════════════════════════════════════════════════════════════════════
# Entry point — stdio transport
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    mcp.run(transport="stdio")
