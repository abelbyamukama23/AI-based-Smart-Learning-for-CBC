/**
 * AppLayout.jsx — Main authenticated application layout
 * Sidebar nav (desktop) + top bar (mobile) + page content area
 */

import { useState, useRef, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { useAuth } from "../hooks/useAuth";
import { getProfile } from "../services/auth.service";
import {
  CBCLogo,
  MwalimuLogo,
  IconGrid,
  IconBook,
  IconLibrary,
  IconBot,
  IconFeed,
  IconLogout,
  IconMenu,
  IconSettings,
  IconUser,
  IconChevronDown,
  IconCollaborate,
  IconBilling,
  IconCompetency,
  IconUsage,
  IconTokens,
} from "../components/Icons";

// ── Nav groups per role ───────────────────────────────────────────────────────
const LEARNER_NAV_GROUPS = [
  {
    title: "Platform",
    items: [
      { to: "/learner/dashboard",     label: "Dashboard",        icon: <IconGrid /> },
      { to: "/learner/lessons",       label: "Lessons",          icon: <IconBook /> },
      { to: "/learner/library",       label: "Library",          icon: <IconLibrary /> },
      { to: "/learner/tutor",         label: "Mwalimu",          icon: <MwalimuLogo size={18} /> },
      { to: "/learner/feed",          label: "Feed",             icon: <IconFeed /> },
      { to: "/learner/collaborate",   label: "Collaborate",      icon: <IconCollaborate /> },
      { to: "/learner/competencies",  label: "My Competencies",  icon: <IconCompetency /> },
    ],
  },
  {
    title: "Billing & Subscription",
    items: [
      { to: "/learner/billing",  label: "Billing", icon: <IconBilling /> },
      { to: "/learner/usage",   label: "Usage",   icon: <IconUsage /> },
      { to: "/learner/tokens",  label: "Tokens",  icon: <IconTokens /> },
    ],
  },
];

const SYSTEM_NAV = (role) => [
  { to: `/${role}/settings`, label: "Settings", icon: <IconSettings size={18} /> },
];

const TEACHER_NAV_GROUPS = [
  {
    title: "Platform",
    items: [
      { to: "/teacher/dashboard", label: "Dashboard", icon: <IconGrid /> },
      { to: "/teacher/lessons",   label: "Lessons",   icon: <IconBook /> },
      { to: "/teacher/library",   label: "Library",   icon: <IconLibrary /> },
      { to: "/teacher/feed",      label: "Feed",      icon: <IconFeed /> },
    ],
  },
  {
    title: "Billing & Subscription",
    items: [
      { to: "/teacher/billing", label: "Billing", icon: <IconBilling /> },
    ],
  },
];

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const { logout, logoutLoading } = useAuth();
  const navigate = useNavigate();

  // Fetch full profile on mount to hydrate the store with name/email
  useEffect(() => {
    let mounted = true;
    getProfile().then((profileData) => {
      if (mounted) {
        setUser(profileData);
      }
    }).catch(console.error);
    return () => { mounted = false; };
  }, [setUser]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isTeacher = user?.role === "TEACHER";
  const navGroups = isTeacher ? TEACHER_NAV_GROUPS : LEARNER_NAV_GROUPS;
  const role = isTeacher ? "teacher" : "learner";
  const systemItems = SYSTEM_NAV(role);
  const initials = getInitials(user);

  return (
    <div className="app-layout">
      {/* ── Sidebar (desktop) ───────────────────────────────────────────── */}
      <aside className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}>
        {/* Logo */}
        <div className="sidebar__logo">
          <CBCLogo />
          <span className="sidebar__logo-text">Mwalimu AI</span>
        </div>

        {/* Navigation — grouped */}
        <nav className="sidebar__nav" aria-label="Main navigation">
          {navGroups.map((group) => (
            <div key={group.title} className="sidebar__nav-group">
              <span className="sidebar__nav-group-title">{group.title}</span>
              {group.items.map((item) => (
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
            </div>
          ))}
        </nav>

        {/* System group — pinned to bottom */}
        <div className="sidebar__nav-group sidebar__nav-group--system">
          <span className="sidebar__nav-group-title">System</span>
          {systemItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar__nav-item ${isActive ? "sidebar__nav-item--active" : ""}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <span className="sidebar__nav-icon" aria-hidden>{item.icon}</span>
              <span className="sidebar__nav-label">{item.label}</span>
            </NavLink>
          ))}
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
            <span>Mwalimu AI</span>
          </div>
          <div className="topbar__avatar" aria-label={`Logged in as ${user?.email}`}>
            {initials}
          </div>
        </header>

        {/* User Account Control (Desktop) */}
        <div className="desktop-account-control" ref={dropdownRef}>
          <button 
            className="user-dropdown-trigger"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-haspopup="true"
            aria-expanded={dropdownOpen}
          >
            <div className="sidebar__user-info">
              <span className="sidebar__user-name">
                {user?.first_name
                  ? `${user.first_name} ${user.last_name || ""}`.trim()
                  : user?.email}
              </span>
              <span className="sidebar__user-role">{formatRole(user?.role)}</span>
            </div>
            <div className="sidebar__avatar" aria-hidden>{initials}</div>
            <IconChevronDown size={16} className="user-dropdown-chevron" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="user-dropdown-menu">
              <div className="user-dropdown-header">
                <p className="user-dropdown-name">
                  {user?.first_name
                    ? `${user.first_name} ${user.last_name || ""}`.trim()
                    : "User"}
                </p>
                <p className="user-dropdown-email">{user?.email}</p>
              </div>
              <button 
                className="user-dropdown-item" 
                onClick={() => {
                  setDropdownOpen(false);
                  navigate(`/${user?.role?.toLowerCase() || 'learner'}/profile`);
                }}
              >
                <IconUser size={16} />
                Manage Account
              </button>
              <button 
                className="user-dropdown-item" 
                onClick={() => {
                  setDropdownOpen(false);
                  navigate(`/${user?.role?.toLowerCase() || 'learner'}/settings`);
                }}
              >
                <IconSettings size={16} />
                Settings
              </button>
              <div className="user-dropdown-divider" />
              <button
                className="user-dropdown-item user-dropdown-item--danger"
                onClick={logout}
                disabled={logoutLoading}
              >
                <IconLogout size={16} />
                Sign out
              </button>
            </div>
          )}
        </div>

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
