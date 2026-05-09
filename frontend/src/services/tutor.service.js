/**
 * tutor.service.js — Mwalimu AI Tutor API Service (Threaded)
 *
 * Endpoints:
 *   POST /api/v1/tutor/ask/              → SSE stream (progress + final answer)
 *   GET  /api/v1/tutor/threads/          → list of ChatThread summaries
 *   GET  /api/v1/tutor/threads/{id}/     → Full ChatThread with all interactions
 *
 * Token handling:
 *   Non-streaming endpoints use api.js (axios) which auto-refreshes on 401.
 *   The SSE endpoint uses raw fetch (axios can't stream) but calls getValidToken()
 *   first to proactively refresh an expired or near-expired access token.
 */

import api from "../lib/api";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

// ── Token refresh helper for raw fetch (SSE) calls ────────────────────────────
/**
 * Returns a valid access token, silently refreshing if expired or within
 * 60 seconds of expiry. Redirects to /login if refresh fails.
 */
async function getValidToken() {
  const access  = localStorage.getItem("access_token");
  const refresh = localStorage.getItem("refresh_token");

  if (!access) return null;

  // Decode JWT payload (pure base64 — no library needed)
  try {
    const payload   = JSON.parse(atob(access.split(".")[1]));
    const expiresAt = payload.exp * 1000; // convert to ms
    const BUFFER    = 60 * 1000;          // refresh 60s before expiry

    if (Date.now() < expiresAt - BUFFER) {
      return access; // still valid
    }
  } catch {
    // malformed token — fall through to refresh
  }

  if (!refresh) {
    window.location.href = "/login";
    return null;
  }

  try {
    const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ refresh }),
    });

    if (!res.ok) throw new Error("Refresh failed");

    const data = await res.json();
    localStorage.setItem("access_token", data.access);
    if (data.refresh) localStorage.setItem("refresh_token", data.refresh);
    return data.access;
  } catch {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    return null;
  }
}

// ── Streaming endpoint ─────────────────────────────────────────────────────────
/**
 * Send a question to Mwalimu using SSE streaming.
 *
 * @param {string}      query           - The learner's question.
 * @param {string|null} threadId        - UUID of the active thread (null = new thread).
 * @param {string|null} contextLessonId - UUID of the open lesson (optional).
 * @param {Function}    onMessage       - Callback fired for every SSE event object.
 * @param {File|null}   imageFile       - Optional image of handwritten work.
 *
 * @returns {Promise<{ threadId, response, provider, ... }>}
 */
export async function askTutor(
  query,
  threadId        = null,
  contextLessonId = null,
  onMessage       = null,
  imageFile       = null
) {
  // Proactively refresh token before opening the SSE stream
  const token = await getValidToken();

  let body;
  let extraHeaders = {};

  if (imageFile) {
    const form = new FormData();
    form.append("query", query);
    if (threadId)        form.append("thread_id",         threadId);
    if (contextLessonId) form.append("context_lesson_id", contextLessonId);
    form.append("image", imageFile);
    body = form;
    // Do NOT set Content-Type — browser adds multipart boundary automatically
  } else {
    const payload = { query };
    if (threadId)        payload.thread_id         = threadId;
    if (contextLessonId) payload.context_lesson_id = contextLessonId;
    body         = JSON.stringify(payload);
    extraHeaders = { "Content-Type": "application/json" };
  }

  const response = await fetch(`${BASE_URL}/tutor/ask/`, {
    method:  "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extraHeaders,
    },
    body,
  });

  if (response.status === 401) {
    // Even after refresh we got 401 — session fully expired
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(`Tutor API error: ${response.status}`);
  }

  // Parse SSE stream
  const reader  = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = { threadId, response: null };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(line.slice(6).trim());
        if (onMessage) onMessage(data);

        if (data.type === "thread_created") {
          result.threadId    = data.thread_id;
          result.threadTitle = data.title;
        }
        if (data.type === "final") {
          result.response       = data.content;
          result.is_out_of_scope = data.is_out_of_scope;
          result.provider       = data.provider;
        }
        if (data.type === "saved") {
          result.interactionId = data.interaction_id;
          result.threadId      = data.thread_id;
        }
      } catch (e) {
        console.error("Error parsing SSE chunk:", e, line);
      }
    }
  }

  return result;
}

// ── Non-streaming endpoints (use api.js — auto-refreshes on 401) ───────────────

/**
 * List all chat threads for the current learner (sidebar).
 * @returns {Promise<ChatThreadSummary[]>}
 */
export async function getChatThreads() {
  const { data } = await api.get("/tutor/threads/");
  return Array.isArray(data) ? data : (data.results ?? []);
}

/**
 * Get a full chat thread with all interaction turns.
 * @param {string} threadId - UUID of the thread.
 * @returns {Promise<ChatThread>}
 */
export async function getChatThread(threadId) {
  const { data } = await api.get(`/tutor/threads/${threadId}/`);
  return data;
}
