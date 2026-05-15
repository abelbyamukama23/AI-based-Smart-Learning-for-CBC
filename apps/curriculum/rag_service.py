"""
apps/curriculum/rag_service.py
───────────────────────────────
Library Agent RAG Service — Refactored

Design Patterns applied:
  • Cache-Aside Pattern  — results cached via Django's cache framework
    (Redis-ready: configure CACHES in settings.py to switch backends).
    Cross-worker sharing is now possible; the old per-process dict is gone.
  • Circuit Breaker      — raises RAGServiceError on ChromaDB failure instead
    of silently returning [].  Callers decide how to handle the open circuit.
  • Named Constants      — all magic numbers imported from constants.py.
  • SRP                  — this module only handles vector search and embedding;
    indexing helpers (_quick_index) live in research_agent.py which owns them.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

from django.core.cache import cache

from .constants import (
    LIBRARY_RAG_DEFAULT_HITS,
    RAG_CACHE_TTL_SECONDS,
    RAG_EMBED_DIMENSION,
    RAG_EXCERPT_MAX_CHARS,
    RAG_RELEVANCE_THRESHOLD,
)
from .exceptions import EmbeddingError, RAGServiceError

logger = logging.getLogger(__name__)

# ── Module-level ChromaDB singleton ───────────────────────────────────────────
_chroma_client = None


def _cache_key(query: str, subject: str, class_level: str) -> str:
    raw = f"{query}|{subject}|{class_level}"
    return f"rag:{hashlib.md5(raw.encode()).hexdigest()}"


# ── ChromaDB client (lazy singleton) ──────────────────────────────────────────

def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from django.conf import settings
        path = settings.CHROMADB_PATH
        Path(path).mkdir(parents=True, exist_ok=True)
        try:
            _chroma_client = chromadb.PersistentClient(path=path)
            logger.info("ChromaDB client initialised at %s", path)
        except Exception as exc:
            raise RAGServiceError(f"ChromaDB failed to initialise: {exc}") from exc
    return _chroma_client


# ── Embedding (Gemini API) ─────────────────────────────────────────────────────

def _embed(text: str, task_type: str = "retrieval_query") -> list[float]:
    """
    Embed text using Google Gemini text-embedding-004.

    Raises:
        EmbeddingError: When the API call fails (callers decide fallback strategy).
    """
    try:
        import google.generativeai as genai
        from django.conf import settings

        api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model="models/gemini-embedding-2",
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(f"Gemini embedding API failed: {exc}") from exc


def embed_for_query(text: str) -> list[float]:
    """Embed a search query.  Falls back to zero-vector on EmbeddingError."""
    try:
        return _embed(text, task_type="retrieval_query")
    except EmbeddingError as exc:
        logger.warning("Embedding failed — returning zero vector: %s", exc)
        return [0.0] * RAG_EMBED_DIMENSION


def embed_for_indexing(text: str) -> list[float]:
    """Embed a document for indexing.  Falls back to zero-vector on EmbeddingError."""
    try:
        return _embed(text, task_type="retrieval_document")
    except EmbeddingError as exc:
        logger.warning("Embedding (indexing) failed — returning zero vector: %s", exc)
        return [0.0] * RAG_EMBED_DIMENSION


# ── Warm-up ────────────────────────────────────────────────────────────────────

def warm_up_rag():
    """Pre-open the ChromaDB file in a background thread to avoid first-request lag."""
    import threading

    def _warmup():
        try:
            _get_chroma_client()
            logger.info("[RAG warm-up] ChromaDB ready (Gemini embedding mode)")
        except RAGServiceError as exc:
            logger.warning("[RAG warm-up] ChromaDB not available: %s", exc)

    threading.Thread(target=_warmup, daemon=True, name="rag-warmup").start()


# ── Search ─────────────────────────────────────────────────────────────────────

def search_library(
    query: str,
    subject: str = "",
    class_level: str = "",
    n_results: int = LIBRARY_RAG_DEFAULT_HITS,
) -> list[dict]:
    """
    Vector-similarity search over curriculum lessons and library files.

    Cache-Aside Pattern:
      1. Check Django cache (shared across all worker processes).
      2. On miss: query ChromaDB, store result in cache.

    Raises:
        RAGServiceError: When ChromaDB is completely unavailable.
                         The MCP tool catches this and falls back gracefully.
    """
    key = _cache_key(query, subject, class_level)
    cached = cache.get(key)
    if cached is not None:
        logger.debug("RAG cache hit: %.60s", query)
        return cached

    try:
        client    = _get_chroma_client()
        embedding = embed_for_query(query)

        where = {}
        if subject:
            where["subject"] = {"$eq": subject}
        if class_level:
            where["class_level"] = {"$eq": class_level}

        query_kwargs = {
            "query_embeddings": [embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
            **( {"where": where} if where else {} ),
        }

        results: list[dict] = []
        for collection_name in ("curriculum_lessons", "curriculum_files"):
            try:
                col  = client.get_collection(collection_name)
                hits = col.query(**query_kwargs)
            except Exception as e:
                logger.debug("RAG collection %s unavailable: %s", collection_name, e)
                continue

            for doc, meta, dist in zip(
                hits["documents"][0],
                hits["metadatas"][0],
                hits["distances"][0],
            ):
                relevance = round(1 - dist, 3)
                if relevance < RAG_RELEVANCE_THRESHOLD:
                    continue
                results.append({
                    "title":       meta.get("title", ""),
                    "subject":     meta.get("subject", ""),
                    "class_level": meta.get("class_level", ""),
                    "type":        meta.get("type", collection_name.replace("curriculum_", "")),
                    "file_type":   meta.get("file_type", ""),
                    "source":      meta.get("source", ""),
                    "tags":        meta.get("tags", ""),
                    "file_id":     meta.get("file_id", ""),
                    "has_content": meta.get("has_content", False),
                    "excerpt":     doc[:RAG_EXCERPT_MAX_CHARS],
                    "relevance":   relevance,
                })

        results.sort(key=lambda x: x["relevance"], reverse=True)
        final = results[:n_results]

        cache.set(key, final, timeout=RAG_CACHE_TTL_SECONDS)
        return final

    except RAGServiceError:
        raise
    except Exception as exc:
        raise RAGServiceError(f"Unexpected vector search error: {exc}") from exc


# ── Lesson compilation helper ──────────────────────────────────────────────────

def compile_lesson(material_title: str, topic: str, excerpts: list[str]) -> dict:
    combined = "\n\n".join(excerpts[:3])
    return {
        "topic":           topic,
        "source_material": material_title,
        "context":         combined,
        "instruction": (
            f"Using the following curriculum material about '{topic}', "
            "compile: (1) Key Lessons, (2) Real-world Application in Uganda, "
            "(3) Main Message, (4) Three Challenge Questions for learners.\n\n"
            f"{combined}"
        ),
    }
