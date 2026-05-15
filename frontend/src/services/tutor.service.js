import api from "../lib/api";
import useAuthStore from "../store/authStore";
import { decodeJWT } from "../lib/utils";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

// ── Token refresh helper for raw fetch (SSE) calls ────────────────────────────
/**
 * Returns a valid access token via the Zustand store (single source of truth).
 * Silently refreshes when the token is expired or within 60 s of expiry.
 * Redirects to /login if refresh fails.
 *
 * Previously read directly from localStorage — now reads/writes through the
 * store so the service and the rest of the app always see the same token state.
 */
async function getValidToken() {
  const { accessToken, refreshToken, setTokens, clearAuth } =
    useAuthStore.getState();

  if (!accessToken) return null;

  // Decode to check expiry — reuse the shared utility, no inline atob()
  try {
    const payload   = decodeJWT(accessToken);
    const expiresAt = payload?.exp * 1000; // ms
    const BUFFER    = 60 * 1000;           // refresh 60 s before expiry

    if (Date.now() < expiresAt - BUFFER) {
      return accessToken; // still valid
    }
  } catch {
    // malformed token — fall through to refresh
  }

  if (!refreshToken) {
    clearAuth();
    window.location.href = "/login";
    return null;
  }

  try {
    const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ refresh: refreshToken }),
    });

    if (!res.ok) throw new Error("Refresh failed");

    const data = await res.json();
    // Update the store — this also persists to localStorage via the store action
    setTokens({ access: data.access, refresh: data.refresh ?? refreshToken });
    return data.access;
  } catch {
    clearAuth();
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
  imageFile       = null,
  mode            = "default",
  signal          = null    // AbortSignal from AbortController
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
    form.append("mode", mode);
    form.append("image", imageFile);
    body = form;
    // Do NOT set Content-Type — browser adds multipart boundary automatically
  } else {
    const payload = { query, mode };
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
    ...(signal ? { signal } : {}),   // wire in the AbortController signal
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
 * @param {string} searchQuery - Optional search term to filter threads.
 * @returns {Promise<ChatThreadSummary[]>}
 */
export async function getChatThreads(searchQuery = "") {
  const url = searchQuery ? `/tutor/threads/?q=${encodeURIComponent(searchQuery)}` : "/tutor/threads/";
  const { data } = await api.get(url);
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
