"""
Research Agent — Autonomous curriculum content discovery pipeline
────────────────────────────────────────────────────────────────
Workflow:
  1. Search DuckDuckGo for Uganda CBC-related resources on a given topic
  2. Download and extract text (web pages + PDFs)
  3. Score relevance to Uganda CBC curriculum using DeepSeek
  4. Score >= AUTO_APPROVE_THRESHOLD  → upload to R2 + create CurriculumFile (auto-approved)
  5. Score >= SAVE_THRESHOLD          → save as ResearchEntry (PENDING, admin reviews)
  6. Score < SAVE_THRESHOLD           → discard silently

Can be called:
  - Via MCP tool (Mwalimu triggers it when library returns empty results)
  - Via management command: python manage.py run_research_agent --topic "Photosynthesis"
"""
import io
import logging
import os
import re
import uuid
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Thresholds ─────────────────────────────────────────────────────────────────
AUTO_APPROVE_THRESHOLD = 0.80   # Auto-add to library
SAVE_THRESHOLD         = 0.50   # Save as pending for admin review
REQUEST_TIMEOUT        = 15     # Seconds
MAX_TEXT_LENGTH        = 8000   # Characters to pass to LLM for scoring


# ── Text extraction helpers ────────────────────────────────────────────────────

def _extract_text_from_url(url: str) -> tuple[str, str]:
    """
    Fetch a URL and extract clean text.
    Returns (text, detected_content_type) where content_type is 'pdf' or 'html'.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; CBC-Research-Agent/1.0; "
                "+https://cbc.edu.ug/bot)"
            )
        }
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()

        if "pdf" in content_type or url.lower().endswith(".pdf"):
            return _extract_pdf_text(resp.content), "pdf"
        else:
            return _extract_html_text(resp.text), "html"

    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return "", "unknown"


def _extract_pdf_text(raw_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages[:20]:   # Cap at 20 pages
            pages.append(page.extract_text() or "")
        return "\n".join(pages)[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.warning(f"PDF extraction failed: {e}")
        return ""


def _extract_html_text(html: str) -> str:
    """Extract clean readable text from HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script / style / nav junk
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.warning(f"HTML extraction failed: {e}")
        return ""


# ── Relevance scoring ──────────────────────────────────────────────────────────

def _score_relevance(text: str, topic: str, subject: str = "") -> float:
    """
    Ask DeepSeek to score how relevant this content is to the Uganda CBC curriculum.
    Returns a float 0.0–1.0.
    """
    try:
        from decouple import config
        from openai import OpenAI

        api_key = config("DEEPSEEK_API_KEY", default="")
        if not api_key:
            # Fallback: keyword-based scoring
            return _keyword_score(text, topic)

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        prompt = (
            f"You are evaluating educational content for the Uganda "
            f"Competence-Based Curriculum (CBC).\n\n"
            f"Topic of interest: {topic}\n"
            f"Subject: {subject or 'General'}\n\n"
            f"Content excerpt:\n{text[:3000]}\n\n"
            f"Rate how relevant this content is to the Uganda CBC curriculum "
            f"on a scale from 0.0 (completely irrelevant) to 1.0 (perfectly relevant "
            f"and accurate CBC curriculum material). "
            f"Respond with ONLY a decimal number like 0.85. No explanation."
        )
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        raw = resp.choices[0].message.content.strip()
        score = float(re.search(r"[\d.]+", raw).group())
        return max(0.0, min(1.0, score))

    except Exception as e:
        logger.warning(f"LLM scoring failed, using keyword fallback: {e}")
        return _keyword_score(text, topic)


def _keyword_score(text: str, topic: str) -> float:
    """Keyword-based fallback relevance score."""
    keywords = [
        "uganda", "cbc", "competence", "curriculum", "ncdc",
        "primary", "secondary", "learner", "lesson", "term",
        topic.lower(),
    ]
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return min(1.0, hits / len(keywords))


# ── R2 upload helper ───────────────────────────────────────────────────────────

def _upload_to_r2(content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload bytes to Cloudflare R2 and return the storage path (key).
    """
    import boto3
    from django.conf import settings

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    key = f"library/research/{filename}"
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=content_type,
    )
    return key


# ── Main research pipeline ─────────────────────────────────────────────────────

def research_and_save(
    topic: str,
    subject: str = "",
    class_level: str = "",
    max_sources: int = 3,
) -> dict:
    """
    Full Research Agent pipeline for a given topic.
    Returns a summary dict of what was saved/discarded.
    """
    from duckduckgo_search import DDGS
    from django.conf import settings

    results = {
        "topic": topic,
        "sources_checked": 0,
        "auto_approved": [],
        "pending_review": [],
        "discarded": 0,
    }

    # ── 1. Search for relevant sources ─────────────────────────────────────────
    search_query = f"Uganda CBC competence based curriculum {subject} {topic} filetype:pdf OR lesson plan OR study guide"
    try:
        hits = list(DDGS().text(search_query, max_results=max_sources * 2))
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return results

    # ── 2. Process each hit ────────────────────────────────────────────────────
    processed = 0
    for hit in hits:
        if processed >= max_sources:
            break

        url   = hit.get("href", "")
        title = hit.get("title", topic)[:255]
        if not url:
            continue

        results["sources_checked"] += 1

        # Extract text
        text, detected_type = _extract_text_from_url(url)
        if len(text) < 100:
            results["discarded"] += 1
            continue

        # Score relevance
        score = _score_relevance(text, topic, subject)
        logger.info(f"Research Agent: {url[:60]} → score={score:.2f}")

        if score < SAVE_THRESHOLD:
            results["discarded"] += 1
            continue

        # Determine subject/level FKs
        subject_obj     = _resolve_subject(subject)
        class_level_obj = _resolve_level(class_level)

        if score >= AUTO_APPROVE_THRESHOLD:
            # ── AUTO-APPROVE: upload to R2 and create CurriculumFile ────────────
            try:
                from apps.curriculum.models import CurriculumFile, FileType

                # Re-download for actual file upload
                raw_bytes = requests.get(url, timeout=REQUEST_TIMEOUT).content
                ext       = "pdf" if detected_type == "pdf" else "html"
                filename  = f"{uuid.uuid4().hex}.{ext}"
                ctype     = "application/pdf" if ext == "pdf" else "text/html"

                # Only upload to R2 if configured; else store as text-only entry
                file_key = ""
                if getattr(settings, "AWS_ACCESS_KEY_ID", ""):
                    file_key = _upload_to_r2(raw_bytes, filename, ctype)

                cf = CurriculumFile.objects.create(
                    title       = title,
                    description = text[:500],
                    file_type   = FileType.PDF if ext == "pdf" else FileType.OTHER,
                    file        = file_key or f"library/research/{filename}",
                    subject     = subject_obj,
                    class_level = class_level_obj,
                    tags        = topic,
                    source      = url[:200],
                )

                # Immediately index into ChromaDB
                _quick_index(str(cf.id), title, text, subject, class_level)
                cf.is_indexed = True
                from django.utils import timezone
                cf.indexed_at = timezone.now()
                cf.save(update_fields=["is_indexed", "indexed_at"])

                results["auto_approved"].append({"title": title, "score": score, "url": url})
                processed += 1

            except Exception as e:
                logger.error(f"Auto-approve failed for {url}: {e}")

        else:
            # ── PENDING REVIEW: save as ResearchEntry ────────────────────────────
            try:
                from apps.curriculum.models import ResearchEntry

                entry, created = ResearchEntry.objects.get_or_create(
                    source_url=url,
                    defaults={
                        "topic":           topic,
                        "title":           title,
                        "content":         text[:5000],
                        "relevance_score": score,
                        "subject":         subject_obj,
                        "class_level":     class_level_obj,
                        "status":          ResearchEntry.Status.PENDING,
                    },
                )
                if created:
                    results["pending_review"].append({"title": title, "score": score, "url": url})
                processed += 1

            except Exception as e:
                logger.error(f"Failed to save ResearchEntry for {url}: {e}")

    return results


def _resolve_subject(name: str):
    if not name:
        return None
    try:
        from apps.curriculum.models import Subject
        return Subject.objects.filter(subject_name__icontains=name).first()
    except Exception:
        return None


def _resolve_level(name: str):
    if not name:
        return None
    try:
        from apps.curriculum.models import Level
        return Level.objects.filter(level_name__iexact=name).first()
    except Exception:
        return None


def _quick_index(file_id: str, title: str, text: str, subject: str, class_level: str):
    """
    Immediately embed a single document into ChromaDB without a full rebuild.

    Bug fix: previously called `_get_embed_model()` which was removed when the
    embedding backend switched from sentence-transformers to the Gemini API.
    Now correctly calls `embed_for_indexing()` from the updated rag_service.
    """
    try:
        from apps.curriculum.rag_service import _get_chroma_client, embed_for_indexing

        client    = _get_chroma_client()
        embedding = embed_for_indexing(text[:4000])   # ← Correct API (was _get_embed_model)
        col       = client.get_or_create_collection(
            "curriculum_files", metadata={"hnsw:space": "cosine"}
        )
        col.upsert(
            ids        = [f"file_{file_id}"],
            embeddings = [embedding],
            documents  = [text[:4000]],
            metadatas  = [{
                "title":       title,
                "file_type":   "auto",
                "subject":     subject,
                "class_level": class_level,
                "tags":        "",
                "source":      "research_agent",
                "file_id":     file_id,
            }],
        )
        logger.info("Quick-indexed file %s into ChromaDB", file_id)
    except Exception as e:
        logger.warning("Quick index failed for %s: %s", file_id, e)

