/**
 * ProtectedRoute.jsx — Guards routes that require authentication.
 * Redirects unauthenticated users to /login.
 * Supports optional role restriction.
 */

import { Navigate, Outlet, useLocation } from "react-router-dom";
import useAuthStore from "../../store/authStore";

export function ProtectedRoute({ allowedRoles }) {
  const location = useLocation();
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  if (!accessToken) {
    // Not authenticated — redirect to login, preserve intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user?.role && !allowedRoles.includes(user.role)) {
    // Authenticated but wrong role — redirect to appropriate dashboard
    const fallback =
      user.role === "TEACHER" ? "/teacher/dashboard" : "/learner/dashboard";
    return <Navigate to={fallback} replace />;
  }

  return <Outlet />;
}

/**
 * GuestRoute — Redirects authenticated users away from auth pages.
 */
export function GuestRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  if (accessToken) {
    const dash =
      user?.role === "TEACHER" ? "/teacher/dashboard" : "/learner/dashboard";
    return <Navigate to={dash} replace />;
  }

  return <Outlet />;
}
