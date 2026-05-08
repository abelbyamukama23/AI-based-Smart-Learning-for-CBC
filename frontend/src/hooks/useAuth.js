/**
 * useAuth.js — Custom hook wrapping auth store + service calls
 *
 * Provides login, register, logout actions with loading/error state
 * already handled, so pages stay clean.
 */

import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import * as authService from "../services/auth.service";
import { extractApiError, extractFieldErrors } from "../lib/utils";

export function useAuth() {
  const navigate = useNavigate();
  const { setTokens, setUser, clearAuth, user, accessToken } = useAuthStore();

  const isAuthenticated = !!accessToken;

  // ── Login ─────────────────────────────────────────────────────────────────
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const login = useCallback(
    async (email, password) => {
      setLoginLoading(true);
      setLoginError(null);
      try {
        const data = await authService.login(email, password);
        setTokens({ access: data.access, refresh: data.refresh });
        // Redirect based on role embedded in JWT
        const role = data.role || useAuthStore.getState().user?.role;
        navigate(role === "TEACHER" ? "/teacher/dashboard" : "/learner/dashboard", {
          replace: true,
        });
        return { success: true };
      } catch (err) {
        const message = extractApiError(err);
        setLoginError(message);
        return { success: false, error: message };
      } finally {
        setLoginLoading(false);
      }
    },
    [navigate, setTokens]
  );

  // ── Register ──────────────────────────────────────────────────────────────
  const [registerLoading, setRegisterLoading] = useState(false);
  const [registerError, setRegisterError] = useState(null);
  const [registerFieldErrors, setRegisterFieldErrors] = useState({});

  const register = useCallback(
    async (payload) => {
      setRegisterLoading(true);
      setRegisterError(null);
      setRegisterFieldErrors({});
      try {
        const data = await authService.register(payload);
        // Backend returns tokens on register — log user in immediately
        setTokens({ access: data.tokens.access, refresh: data.tokens.refresh });
        setUser(data.user);
        const role = data.user?.role;
        navigate(role === "TEACHER" ? "/teacher/dashboard" : "/learner/dashboard", {
          replace: true,
        });
        return { success: true };
      } catch (err) {
        const message = extractApiError(err);
        const fields = extractFieldErrors(err);
        setRegisterError(message);
        setRegisterFieldErrors(fields);
        return { success: false, error: message, fields };
      } finally {
        setRegisterLoading(false);
      }
    },
    [navigate, setTokens, setUser]
  );

  // ── Logout ────────────────────────────────────────────────────────────────
  const [logoutLoading, setLogoutLoading] = useState(false);

  const logout = useCallback(async () => {
    setLogoutLoading(true);
    try {
      const refresh = useAuthStore.getState().refreshToken;
      if (refresh) await authService.logout(refresh);
    } catch {
      // Even if server-side blacklisting fails, still clear local state
    } finally {
      clearAuth();
      setLogoutLoading(false);
      navigate("/login", { replace: true });
    }
  }, [clearAuth, navigate]);

  return {
    // State
    user,
    isAuthenticated,
    // Login
    login,
    loginLoading,
    loginError,
    // Register
    register,
    registerLoading,
    registerError,
    registerFieldErrors,
    // Logout
    logout,
    logoutLoading,
  };
}
