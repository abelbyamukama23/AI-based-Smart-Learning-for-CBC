/**
 * DashboardPlaceholder.jsx — Temporary placeholder dashboards.
 * Will be replaced with real dashboard pages as features are built.
 */

import { Link } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import { useAuth } from "../../hooks/useAuth";

export function LearnerDashboard() {
  const user = useAuthStore((s) => s.user);
  const { logout, logoutLoading } = useAuth();

  return (
    <div className="placeholder-page">
      <div className="placeholder-page__card">
        <div className="placeholder-page__avatar" aria-hidden>📚</div>
        <h1 className="placeholder-page__title">
          Welcome, {user?.first_name || user?.email || "Learner"}!
        </h1>
        <p className="placeholder-page__subtitle">
          Your learner dashboard is coming soon. Role:{" "}
          <strong>{user?.role}</strong>
        </p>
        {user?.class_level && (
          <p className="placeholder-page__meta">Class: {user.class_level}</p>
        )}
        <button
          className="btn btn-secondary btn-md"
          onClick={logout}
          disabled={logoutLoading}
        >
          {logoutLoading ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </div>
  );
}

export function TeacherDashboard() {
  const user = useAuthStore((s) => s.user);
  const { logout, logoutLoading } = useAuth();

  return (
    <div className="placeholder-page">
      <div className="placeholder-page__card">
        <div className="placeholder-page__avatar" aria-hidden>🏫</div>
        <h1 className="placeholder-page__title">
          Welcome, {user?.first_name || user?.email || "Teacher"}!
        </h1>
        <p className="placeholder-page__subtitle">
          Your teacher dashboard is coming soon. Role:{" "}
          <strong>{user?.role}</strong>
        </p>
        <button
          className="btn btn-secondary btn-md"
          onClick={logout}
          disabled={logoutLoading}
        >
          {logoutLoading ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </div>
  );
}
