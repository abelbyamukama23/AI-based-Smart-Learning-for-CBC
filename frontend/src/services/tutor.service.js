/**
 * tutor.service.js — Mwalimu AI Tutor API Service (Threaded)
 *
 * Endpoints:
 *   POST /api/v1/tutor/ask/              → SSE stream (progress + final answer)
 *   GET  /api/v1/tutor/threads/          → list of ChatThread summaries
 *   GET  /api/v1/tutor/threads/{id}/     → Full ChatThread with all interactions
 */

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

function authHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/**
 * Send a question to Mwalimu using SSE streaming.
 *
 * @param {string}        query         - The learner's question.
 * @param {string|null}   threadId      - UUID of the active thread (null = new thread).
 * @param {string|null}   contextLessonId - UUID of the open lesson (optional).
 * @param {Function}      onMessage     - Callback fired for every SSE event object.
 *
 * @returns {Promise<{ threadId: string, response: string, ... }>}
 */
export async function askTutor(
  query,
  threadId = null,
  contextLessonId = null,
  onMessage = null,
  imageFile = null
) {
  // Build request body — multipart when image attached, JSON otherwise
  let body;
  let extraHeaders = {};

  if (imageFile) {
    const form = new FormData();
    form.append("query", query);
    if (threadId) form.append("thread_id", threadId);
    if (contextLessonId) form.append("context_lesson_id", contextLessonId);
    form.append("image", imageFile);
    body = form;
    // Do NOT set Content-Type — browser sets it with boundary automatically
  } else {
    const payload = { query };
    if (threadId) payload.thread_id = threadId;
    if (contextLessonId) payload.context_lesson_id = contextLessonId;
    body = JSON.stringify(payload);
    extraHeaders = { "Content-Type": "application/json" };
  }

  const token = localStorage.getItem("access_token");
  const response = await fetch(`${BASE_URL}/tutor/ask/`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extraHeaders,
    },
    body,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const reader = response.body.getReader();
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
          result.threadId = data.thread_id;
          result.threadTitle = data.title;
        }
        if (data.type === "final") {
          result.response = data.content;
          result.is_out_of_scope = data.is_out_of_scope;
          result.provider = data.provider;
        }
        if (data.type === "saved") {
          result.interactionId = data.interaction_id;
          result.threadId = data.thread_id;
        }
      } catch (e) {
        console.error("Error parsing SSE chunk:", e, line);
      }
    }
  }

  return result;
}

/**
 * List all chat threads for the current learner (sidebar).
 * @returns {Promise<ChatThreadSummary[]>}
 */
export async function getChatThreads() {
  const res = await fetch(`${BASE_URL}/tutor/threads/`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : (data.results ?? []);
}

/**
 * Get a full chat thread with all interaction turns.
 * @param {string} threadId - UUID of the thread.
 * @returns {Promise<ChatThread>}
 */
export async function getChatThread(threadId) {
  const res = await fetch(`${BASE_URL}/tutor/threads/${threadId}/`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
