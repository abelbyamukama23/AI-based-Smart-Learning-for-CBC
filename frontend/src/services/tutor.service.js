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
export async function askTutor(query, contextLessonId = null) {
  const payload = { query };
  if (contextLessonId) {
    payload.context_lesson_id = contextLessonId;
  }
  const { data } = await api.post("/tutor/ask/", payload);
  return data;
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
