/**
 * auth.service.js — CBC Auth API Service Layer
 *
 * Maps directly to backend endpoints:
 *   POST /api/v1/auth/register/
 *   POST /api/v1/auth/login/
 *   POST /api/v1/auth/logout/
 *   POST /api/v1/auth/token/refresh/
 *   GET  /api/v1/auth/me/
 *   PATCH /api/v1/auth/me/
 */

import api from "../lib/api";

/**
 * Register a new user (Learner or Teacher).
 *
 * Learner payload:
 *   { email, password, first_name, last_name, role: "LEARNER",
 *     class_level, school_name, region, district }
 *
 * Teacher payload:
 *   { email, password, first_name, last_name, role: "TEACHER" }
 *
 * @returns {{ message, user, tokens: { access, refresh } }}
 */
export async function register(payload) {
  const { data } = await api.post("/auth/register/", payload);
  return data;
}

/**
 * Login with email + password.
 * Backend uses email as USERNAME_FIELD.
 *
 * @returns {{ access, refresh, ...customClaims }}
 */
export async function login(email, password) {
  const { data } = await api.post("/auth/login/", { email, password });
  return data;
}

/**
 * Logout — blacklists the refresh token on the server.
 * @param {string} refreshToken
 */
export async function logout(refreshToken) {
  await api.post("/auth/logout/", { refresh: refreshToken });
}

/**
 * Get the current authenticated user's profile.
 * @returns {User}
 */
export async function getProfile() {
  const { data } = await api.get("/auth/me/");
  return data;
}

/**
 * Partially update the authenticated user's profile.
 * @param {object} payload
 * @returns {User}
 */
export async function updateProfile(payload) {
  const { data } = await api.patch("/auth/me/", payload);
  return data;
}
