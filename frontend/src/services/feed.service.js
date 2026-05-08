/**
 * feed.service.js — Knowledge Feed API Service
 *
 * Endpoints:
 *   GET    /api/v1/feed/posts/                   → paginated feed
 *   POST   /api/v1/feed/posts/                   → create post
 *   DELETE /api/v1/feed/posts/{id}/              → soft delete
 *   POST   /api/v1/feed/posts/{id}/react/        → { type: "LIKE"|"SHARE" }
 *   GET    /api/v1/feed/posts/{id}/comments/     → get comments
 *   POST   /api/v1/feed/posts/{id}/comments/     → add comment
 */

import api from "../lib/api";

export async function getFeedPosts(params = {}) {
  const { data } = await api.get("/feed/posts/", { params });
  return data; // { count, next, previous, results }
}

export async function getPost(id) {
  const { data } = await api.get(`/feed/posts/${id}/`);
  return data;
}

export async function createPost(payload) {
  // payload can include: content, visibility, photo (File), video (File)
  const isMultipart = payload.photo || payload.video;
  if (isMultipart) {
    const form = new FormData();
    Object.entries(payload).forEach(([k, v]) => {
      if (v !== undefined && v !== null) form.append(k, v);
    });
    const { data } = await api.post("/feed/posts/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }
  const { data } = await api.post("/feed/posts/", payload);
  return data;
}

export async function deletePost(id) {
  await api.delete(`/feed/posts/${id}/`);
}

export async function reactToPost(id, type) {
  const { data } = await api.post(`/feed/posts/${id}/react/`, { type });
  return data; // { action: "liked"|"unliked", type }
}

export async function getComments(postId) {
  const { data } = await api.get(`/feed/posts/${postId}/comments/`);
  return data;
}

export async function addComment(postId, text) {
  const { data } = await api.post(`/feed/posts/${postId}/comments/`, { text });
  return data;
}
