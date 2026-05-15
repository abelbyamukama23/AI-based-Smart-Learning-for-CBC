/**
 * router/index.jsx — Application Route Configuration
 *
 * Route tree:
 *   /                   → redirect to /login
 *   /login              → LoginPage
 *   /register           → RegisterPage
 *   /learner/...        → AppLayout
 *   /teacher/...        → AppLayout
 */

import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "../layouts/AuthLayout";
import { AppLayout } from "../layouts/AppLayout";
import { ProtectedRoute, GuestRoute } from "../components/routing/ProtectedRoute";
import { ErrorBoundary } from "../components/routing/ErrorBoundary";

import LoginPage          from "../pages/auth/LoginPage";
import RegisterPage       from "../pages/auth/RegisterPage";
import LearnerDashboard   from "../pages/dashboard/LearnerDashboard";
import TeacherDashboard   from "../pages/dashboard/TeacherDashboard";
import LessonsPage        from "../pages/lessons/LessonsPage";
import LessonDetailPage   from "../pages/lessons/LessonDetailPage";
import TutorPage          from "../pages/tutor/TutorPage";
import FeedPage           from "../pages/feed/FeedPage";
import FeedPostDetailPage from "../pages/feed/FeedPostDetailPage";
import LibraryPage        from "../pages/library/LibraryPage";
import LearnerSettingsPage from "../pages/settings/LearnerSettingsPage";
import CollaboratePage    from "../pages/collaborate/CollaboratePage";
import CompetenciesPage   from "../pages/competencies/CompetenciesPage";
import UsagePage          from "../pages/billing/UsagePage";
import TokensPage         from "../pages/billing/TokensPage";
import TeacherBillingPlaceholder from "../pages/billing/TeacherBillingPlaceholder";
import LearnerBillingPlaceholder from "../pages/billing/LearnerBillingPlaceholder";

const router = createBrowserRouter([
  // ── Root redirect ──────────────────────────────────────────────────────────
  {
    index: true,
    path: "/",
    element: <Navigate to="/login" replace />,
  },

  // ── Guest routes ───────────────────────────────────────────────────────────
  {
    element: <GuestRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: "/login",    element: <LoginPage /> },
          { path: "/register", element: <RegisterPage /> },
        ],
      },
    ],
  },

  // ── Protected: Learner ─────────────────────────────────────────────────────
  {
    element: <ProtectedRoute allowedRoles={["LEARNER", "ADMIN"]} />,
    children: [
      {
        element: <ErrorBoundary><AppLayout /></ErrorBoundary>,
        children: [
          { path: "/learner/dashboard",  element: <LearnerDashboard /> },
          { path: "/learner/lessons",    element: <LessonsPage /> },
          { path: "/learner/lessons/:id",element: <LessonDetailPage /> },
          { path: "/learner/tutor",      element: <TutorPage /> },
          { path: "/learner/feed",       element: <FeedPage /> },
          { path: "/learner/feed/:id",   element: <FeedPostDetailPage /> },
          { path: "/learner/library",    element: <LibraryPage /> },
          { path: "/learner/settings",     element: <LearnerSettingsPage /> },
          { path: "/learner/collaborate",   element: <CollaboratePage /> },
          { path: "/learner/competencies",  element: <CompetenciesPage /> },
          { path: "/learner/billing",       element: <LearnerBillingPlaceholder /> },
          { path: "/learner/usage",         element: <UsagePage /> },
          { path: "/learner/tokens",        element: <TokensPage /> },
        ],
      },
    ],
  },

  // ── Protected: Teacher ─────────────────────────────────────────────────────
  {
    element: <ProtectedRoute allowedRoles={["TEACHER", "ADMIN"]} />,
    children: [
      {
        element: <ErrorBoundary><AppLayout /></ErrorBoundary>,
        children: [
          { path: "/teacher/dashboard",  element: <TeacherDashboard /> },
          { path: "/teacher/lessons",    element: <LessonsPage /> },
          { path: "/teacher/lessons/:id",element: <LessonDetailPage /> },
          { path: "/teacher/feed",       element: <FeedPage /> },
          { path: "/teacher/feed/:id",   element: <FeedPostDetailPage /> },
          { path: "/teacher/library",    element: <LibraryPage /> },
          { path: "/teacher/billing",    element: <TeacherBillingPlaceholder /> },
        ],
      },
    ],
  },

  // ── 404 fallback ───────────────────────────────────────────────────────────
  { path: "*", element: <Navigate to="/login" replace /> },
]);

export default router;
