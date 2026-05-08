/**
 * utils.js — Shared utility helpers for the CBC Frontend
 */

/**
 * Lightweight JWT payload decoder (no verification — server validates).
 * @param {string} token
 * @returns {object|null}
 */
export function decodeJWT(token) {
  try {
    const base64Payload = token.split(".")[1];
    const decoded = atob(base64Payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * Check if a JWT access token is expired.
 * @param {string} token
 * @returns {boolean}
 */
export function isTokenExpired(token) {
  const payload = decodeJWT(token);
  if (!payload?.exp) return true;
  return Date.now() >= payload.exp * 1000;
}

/**
 * Merge class names conditionally (lightweight clsx alternative).
 * @param {...string} classes
 * @returns {string}
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

/**
 * Extract a readable error message from an Axios error response.
 * Handles DRF error shapes: string, object, and array.
 * @param {import("axios").AxiosError} error
 * @returns {string}
 */
export function extractApiError(error) {
  const data = error?.response?.data;
  if (!data) return error?.message || "Something went wrong. Please try again.";

  // DRF non-field errors
  if (data.non_field_errors) {
    return Array.isArray(data.non_field_errors)
      ? data.non_field_errors.join(" ")
      : data.non_field_errors;
  }

  if (typeof data === "string") return data;
  if (data.detail) return data.detail;

  // Field-level errors → flatten to first message
  const fieldErrors = Object.entries(data)
    .map(([field, msgs]) => {
      const msg = Array.isArray(msgs) ? msgs[0] : msgs;
      return `${field}: ${msg}`;
    })
    .join(". ");

  return fieldErrors || "An unexpected error occurred.";
}

/**
 * Extract field-level errors from a DRF 400 response.
 * Returns a map of { fieldName: "error message" }
 * @param {import("axios").AxiosError} error
 * @returns {Record<string, string>}
 */
export function extractFieldErrors(error) {
  const data = error?.response?.data;
  if (!data || typeof data !== "object") return {};

  const fieldMap = {};
  Object.entries(data).forEach(([field, msgs]) => {
    fieldMap[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
  });
  return fieldMap;
}
