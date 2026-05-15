"""
apps/curriculum/constants.py
─────────────────────────────
Named constants for the curriculum domain.

Design Principle (avoid Magic Numbers):
  All tunable limits live here so changing a threshold requires editing one
  file, not hunting through ORM queries and tool definitions.
"""

# ── Search / query limits ──────────────────────────────────────────────────────
CURRICULUM_SEARCH_LIMIT   = 10   # Max lessons returned by search_curriculum MCP tool
COMPETENCY_LIST_LIMIT     = 20   # Max competencies returned per subject/level
LEARNER_HISTORY_HARD_CAP  = 10   # Absolute maximum history sessions the agent may fetch
LIBRARY_RAG_DEFAULT_HITS  = 5    # Default n_results for vector search

# ── RAG / embedding ────────────────────────────────────────────────────────────
RAG_RELEVANCE_THRESHOLD   = 0.15  # Minimum cosine similarity to include a hit
RAG_EXCERPT_MAX_CHARS     = 800   # Characters of document body returned per hit
RAG_CACHE_TTL_SECONDS     = 120   # How long a query result is cached (2 minutes)
RAG_SEARCH_TIMEOUT_SECS   = 12    # Hard timeout for RAG search to prevent hangs
RAG_EMBED_DIMENSION       = 3072  # gemini-embedding-2 output dimension

# ── Research agent ─────────────────────────────────────────────────────────────
AUTO_APPROVE_THRESHOLD    = 0.80  # Score ≥ this → auto-add to library
SAVE_THRESHOLD            = 0.50  # Score ≥ this → save as pending review
RESEARCH_REQUEST_TIMEOUT  = 15    # HTTP timeout (seconds) when fetching web pages
MAX_TEXT_FOR_LLM          = 8000  # Characters sent to LLM for relevance scoring
PDF_MAX_PAGES             = 20    # Max pages to extract from a PDF

# ── Lesson list pagination ─────────────────────────────────────────────────────
LESSON_LIST_PAGE_SIZE     = 20    # Overrides global DRF page size for lessons
