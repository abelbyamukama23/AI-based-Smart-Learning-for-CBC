/**
 * tutor.service.js — Mwalimu AI Tutor API Service
 *
 * Endpoints:
 *   POST /api/v1/tutor/ask/              → { query, context_lesson_id? } → AISession
 *   GET  /api/v1/tutor/history/          → list of AISession
 *   GET  /api/v1/tutor/history/{id}/     → AISession detail
 *
 * The backend uses an MCP-powered agent that races three LLMs (Gemini,
 * DeepSeek, Claude) simultaneously — whichever responds first wins.
 * The session object includes `llm_provider_used` and `tool_calls_log`
 * so the UI can show which AI answered and what data it looked up.
 */

import api from "../lib/api";

/**
 * Send a question to Mwalimu (the AI Tutor agent).
 *
 * @param {string} query               — The learner's question.
 * @param {string|null} contextLessonId — UUID of the lesson currently open (optional).
 *
 * @returns {Promise<AISession>}
 *   {
 *     id, query, response, flagged_out_of_scope, timestamp, kb_version,
 *     context_lesson, tool_calls_log, llm_provider_used
 *   }
 */
export async function askTutor(query, contextLessonId = null, onMessage = null) {
  const payload = { query };
  if (contextLessonId) {
    payload.context_lesson_id = contextLessonId;
  }
  
  if (!onMessage) {
    // Fallback for non-streaming calls if any
    const { data } = await api.post("/tutor/ask/", payload);
    return data;
  }

  // Streaming approach
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${BASE_URL}/tutor/ask/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  
  let finalSession = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Process SSE lines
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || ""; // Keep the incomplete line in the buffer
    
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const dataStr = line.replace("data: ", "").trim();
          if (!dataStr) continue;
          
          const data = JSON.parse(dataStr);
          onMessage(data);
          
          if (data.type === "final") {
            finalSession = {
              id: Date.now().toString(), // Mock ID until refreshed from history
              query,
              response: data.content,
              flagged_out_of_scope: data.is_out_of_scope,
              timestamp: new Date().toISOString(),
              llm_provider_used: data.provider,
              tool_calls_log: data.tool_calls_log
            };
          }
        } catch (e) {
          console.error("Error parsing SSE JSON:", e, line);
        }
      }
    }
  }
  
  return finalSession || { response: "An error occurred." };
}

/**
 * Get AI session history for the current authenticated learner.
 * @returns {Promise<AISession[]>}
 */
export async function getTutorHistory() {
  const { data } = await api.get("/tutor/history/");
  return data;
}

/**
 * Get a specific AI session by ID.
 * @param {string} id — UUID of the AISession.
 * @returns {Promise<AISession>}
 */
export async function getTutorSession(id) {
  const { data } = await api.get(`/tutor/history/${id}/`);
  return data;
}
