/**
 * library.service.js — CBC Curriculum Library API Service
 *
 * Endpoints (via api.js axios — auto-refreshes JWT on 401):
 *   GET /api/v1/curriculum/library/          → list all library files
 *   GET /api/v1/curriculum/library/{id}/     → single file detail
 *   GET /api/v1/curriculum/library/?search=X → keyword search
 *   GET /api/v1/curriculum/library/?subject_name=Biology
 *   GET /api/v1/curriculum/library/?level_name=S1
 *   GET /api/v1/curriculum/library/?type=PDF
 */

import api from "../lib/api";

/**
 * Fetch library files with optional filters.
 * @param {{ search, subject_name, level_name, type }} filters
 * @returns {Promise<CurriculumFile[]>}
 */
export async function getLibraryFiles(filters = {}) {
  const params = {};
  if (filters.search)       params.search       = filters.search;
  if (filters.subject_name) params.subject_name = filters.subject_name;
  if (filters.level_name)   params.level_name   = filters.level_name;
  if (filters.type)         params.type         = filters.type;

  const { data } = await api.get("/curriculum/library/", { params });
  return Array.isArray(data) ? data : (data.results ?? []);
}

/**
 * Fetch a single library file by ID.
 * @param {string} id - UUID
 * @returns {Promise<CurriculumFile>}
 */
export async function getLibraryFile(id) {
  const { data } = await api.get(`/curriculum/library/${id}/`);
  return data;
}

/**
 * Fetch all available subjects (for filter dropdowns).
 * @returns {Promise<Subject[]>}
 */
export async function getSubjects() {
  const { data } = await api.get("/curriculum/subjects/");
  return Array.isArray(data) ? data : (data.results ?? []);
}

/**
 * Fetch all class levels (for filter dropdowns).
 * @returns {Promise<Level[]>}
 */
export async function getLevels() {
  const { data } = await api.get("/curriculum/class-levels/");
  return Array.isArray(data) ? data : (data.results ?? []);
}
