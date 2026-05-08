/**
 * curriculum.service.js — CBC Curriculum API Service
 *
 * Endpoints:
 *   GET /api/v1/curriculum/subjects/
 *   GET /api/v1/curriculum/class-levels/
 *   GET /api/v1/curriculum/lessons/           ?subject=&class_level=&search=
 *   GET /api/v1/curriculum/lessons/{id}/
 *   GET /api/v1/curriculum/subjects/{id}/competencies/  ?level_id=
 */

import api from "../lib/api";

export async function getSubjects() {
  const { data } = await api.get("/curriculum/subjects/");
  return data;
}

export async function getClassLevels() {
  const { data } = await api.get("/curriculum/class-levels/");
  return data;
}

/**
 * @param {object} params - { subject, class_level, search, page }
 */
export async function getLessons(params = {}) {
  const { data } = await api.get("/curriculum/lessons/", { params });
  return data;
}

export async function getLessonDetail(id) {
  const { data } = await api.get(`/curriculum/lessons/${id}/`);
  return data;
}

export async function getSubjectCompetencies(subjectId, levelId) {
  const params = levelId ? { level_id: levelId } : {};
  const { data } = await api.get(
    `/curriculum/subjects/${subjectId}/competencies/`,
    { params }
  );
  return data;
}
