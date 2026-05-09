"""
Library Agent RAG Service
─────────────────────────
Provides vector-similarity search over the curriculum library (ChromaDB)
and lesson compilation from retrieved materials.

Used by the MCP server tools: search_library, compile_lesson_from_material.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded globals (initialised once on first use)
_chroma_client = None
_embed_model   = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from django.conf import settings
        path = settings.CHROMADB_PATH
        Path(path).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=path)
    return _chroma_client


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def search_library(
    query: str,
    subject: str = "",
    class_level: str = "",
    n_results: int = 5,
) -> list[dict]:
    """
    Vector-similarity search over curriculum lessons and library files.
    Returns a ranked list of matching materials with metadata.
    """
    try:
        client = _get_chroma_client()
        model  = _get_embed_model()
        embedding = model.encode(query).tolist()

        results = []

        for collection_name in ("curriculum_lessons", "curriculum_files"):
            try:
                col = client.get_collection(collection_name)
            except Exception:
                continue  # Collection doesn't exist yet

            # Build where filter
            where = {}
            if subject:
                where["subject"] = {"$eq": subject}
            if class_level:
                where["class_level"] = {"$eq": class_level}

            query_kwargs = {
                "query_embeddings": [embedding],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                query_kwargs["where"] = where

            try:
                hits = col.query(**query_kwargs)
            except Exception as e:
                logger.warning(f"ChromaDB query failed on {collection_name}: {e}")
                continue

            for doc, meta, dist in zip(
                hits["documents"][0],
                hits["metadatas"][0],
                hits["distances"][0],
            ):
                results.append({
                    "title":       meta.get("title", ""),
                    "subject":     meta.get("subject", ""),
                    "class_level": meta.get("class_level", ""),
                    "type":        meta.get("type", collection_name.replace("curriculum_", "")),
                    "file_type":   meta.get("file_type", ""),
                    "source":      meta.get("source", ""),
                    "tags":        meta.get("tags", ""),
                    "file_id":     meta.get("file_id", ""),
                    "excerpt":     doc[:500],
                    "relevance":   round(1 - dist, 3),  # cosine similarity
                })

        # Sort all results by relevance descending
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:n_results]

    except Exception as e:
        logger.error(f"Library search error: {e}")
        return []


def compile_lesson(material_title: str, topic: str, excerpts: list[str]) -> dict:
    """
    Compile a structured lesson summary from retrieved library excerpts.
    Returns: key_lessons, application, main_message, challenge_questions.
    This is a lightweight structured wrapper — actual LLM compilation
    happens in the MCP tool which passes results to Mwalimu.
    """
    combined = "\n\n".join(excerpts[:3])
    return {
        "topic":               topic,
        "source_material":     material_title,
        "context":             combined,
        "instruction": (
            f"Using the following curriculum material about '{topic}', "
            "compile: (1) Key Lessons, (2) Real-world Application in Uganda, "
            "(3) Main Message, (4) Three Challenge Questions for learners.\n\n"
            f"{combined}"
        ),
    }
