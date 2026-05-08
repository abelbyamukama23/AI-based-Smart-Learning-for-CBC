/**
 * authStore.js — Global authentication state (Zustand)
 *
 * Responsibilities:
 *   - Store access/refresh tokens in localStorage
 *   - Hold decoded user object in memory
 *   - Expose login, logout, setUser actions
 *   - Provide isAuthenticated and role-check selectors
 */

import { create } from "zustand";
import { decodeJWT } from "../lib/utils";

/** Keys used for localStorage persistence */
const KEYS = {
  ACCESS: "access_token",
  REFRESH: "refresh_token",
};

function loadInitialUser() {
  const token = localStorage.getItem(KEYS.ACCESS);
  if (!token) return null;
  return decodeJWT(token);
}

const useAuthStore = create((set, get) => ({
  // ── State ──────────────────────────────────────────────────────────────────
  user: loadInitialUser(),           // Decoded JWT payload or full profile obj
  accessToken: localStorage.getItem(KEYS.ACCESS) || null,
  refreshToken: localStorage.getItem(KEYS.REFRESH) || null,
  isLoading: false,

  // ── Derived ───────────────────────────────────────────────────────────────
  isAuthenticated: () => !!get().accessToken,
  role: () => get().user?.role || null,
  isLearner: () => get().user?.role === "LEARNER",
  isTeacher: () => get().user?.role === "TEACHER",
  isAdmin: () => get().user?.role === "ADMIN",

  // ── Actions ───────────────────────────────────────────────────────────────

  /**
   * Called after successful login or register.
   * Persists tokens and decodes user from JWT.
   */
  setTokens: ({ access, refresh }) => {
    localStorage.setItem(KEYS.ACCESS, access);
    localStorage.setItem(KEYS.REFRESH, refresh);
    const decoded = decodeJWT(access);
    set({
      accessToken: access,
      refreshToken: refresh,
      user: decoded,
    });
  },

  /**
   * Override user with full profile from /auth/me/ (richer than JWT claims).
   */
  setUser: (user) => set({ user }),

  /** Set loading state during async auth operations. */
  setLoading: (isLoading) => set({ isLoading }),

  /**
   * Full logout — clears store and localStorage.
   */
  clearAuth: () => {
    localStorage.removeItem(KEYS.ACCESS);
    localStorage.removeItem(KEYS.REFRESH);
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
    });
  },
}));

export default useAuthStore;
