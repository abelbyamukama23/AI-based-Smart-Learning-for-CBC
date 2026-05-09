/**
 * AppLayout.jsx — Main authenticated application layout
 * Sidebar nav (desktop) + top bar (mobile) + page content area
 */

import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { useAuth } from "../hooks/useAuth";

// ── Nav items per role ────────────────────────────────────────────────────────
const LEARNER_NAV = [
  { to: "/learner/dashboard", label: "Dashboard",  icon: <IconGrid /> },
  { to: "/learner/lessons",   label: "Lessons",    icon: <IconBook /> },
  { to: "/learner/library",   label: "Library",    icon: <IconLibrary /> },
  { to: "/learner/tutor",     label: "Mwalimu",    icon: <IconBot /> },
  { to: "/learner/feed",      label: "Feed",       icon: <IconFeed /> },
];

const TEACHER_NAV = [
  { to: "/teacher/dashboard", label: "Dashboard",  icon: <IconGrid /> },
  { to: "/teacher/lessons",   label: "Lessons",    icon: <IconBook /> },
  { to: "/teacher/library",   label: "Library",    icon: <IconLibrary /> },
  { to: "/teacher/feed",      label: "Feed",       icon: <IconFeed /> },
];

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const user = useAuthStore((s) => s.user);
  const { logout, logoutLoading } = useAuth();

  const navItems = user?.role === "TEACHER" ? TEACHER_NAV : LEARNER_NAV;
  const initials = getInitials(user);

  return (
    <div className="app-layout">
      {/* ── Sidebar (desktop) ───────────────────────────────────────────── */}
      <aside className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}>
        {/* Logo */}
        <div className="sidebar__logo">
          <CBCLogo />
          <span className="sidebar__logo-text">CBC Learn</span>
        </div>

        {/* Navigation */}
        <nav className="sidebar__nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `sidebar__nav-item ${isActive ? "sidebar__nav-item--active" : ""}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <span className="sidebar__nav-icon" aria-hidden>{item.icon}</span>
              <span className="sidebar__nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User profile + logout */}
        <div className="sidebar__footer">
          <div className="sidebar__user">
            <div className="sidebar__avatar" aria-hidden>{initials}</div>
            <div className="sidebar__user-info">
              <span className="sidebar__user-name">
                {user?.first_name
                  ? `${user.first_name} ${user.last_name || ""}`.trim()
                  : user?.email}
              </span>
              <span className="sidebar__user-role">{formatRole(user?.role)}</span>
            </div>
          </div>
          <button
            className="sidebar__logout"
            onClick={logout}
            disabled={logoutLoading}
            aria-label="Sign out"
            title="Sign out"
          >
            <IconLogout />
          </button>
        </div>
      </aside>

      {/* ── Mobile overlay ──────────────────────────────────────────────── */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      )}

      {/* ── Main content ────────────────────────────────────────────────── */}
      <div className="app-main">
        {/* Top bar (mobile) */}
        <header className="topbar">
          <button
            className="topbar__menu-btn"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label="Open navigation menu"
          >
            <IconMenu />
          </button>
          <div className="topbar__logo">
            <CBCLogo size={24} />
            <span>CBC Learn</span>
          </div>
          <div className="topbar__avatar" aria-label={`Logged in as ${user?.email}`}>
            {initials}
          </div>
        </header>

        {/* Page content */}
        <main className="app-content" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getInitials(user) {
  if (user?.first_name && user?.last_name)
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
  if (user?.first_name) return user.first_name[0].toUpperCase();
  if (user?.email) return user.email[0].toUpperCase();
  return "U";
}

function formatRole(role) {
  const map = { LEARNER: "Student", TEACHER: "Teacher", ADMIN: "Admin" };
  return map[role] || role;
}

// ── Inline SVG Icons ──────────────────────────────────────────────────────────
function CBCLogo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      <rect width="40" height="40" rx="10" fill="var(--color-primary-600)" />
      <path d="M12 20C12 15.582 15.582 12 20 12C22.21 12 24.21 12.895 25.657 14.343"
        stroke="white" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M28 20C28 24.418 24.418 28 20 28C17.79 28 15.79 27.105 14.343 25.657"
        stroke="white" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="20" cy="20" r="3" fill="white" />
    </svg>
  );
}

function IconGrid() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>;
}
function IconBook() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>;
}
function IconLibrary() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="4" height="18" rx="1"/><rect x="8" y="3" width="4" height="18" rx="1"/><path d="M14 3l4 18"/><path d="M18 3l4 18"/></svg>;
}
function IconBot() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
}
function IconFeed() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>;
}
function IconLogout() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>;
}
function IconMenu() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>;
}
