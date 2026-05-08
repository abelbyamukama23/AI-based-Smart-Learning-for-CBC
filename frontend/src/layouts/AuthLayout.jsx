/**
 * AuthLayout.jsx — Layout wrapper for all authentication pages.
 * Provides the two-panel structure (brand panel + form panel).
 * The actual visual design will be applied after Figma review.
 */

import { Outlet, Link } from "react-router-dom";

export function AuthLayout() {
  return (
    <div className="auth-layout">
      {/* ── Left / Brand Panel ─────────────────────────────────────────────── */}
      <div className="auth-layout__brand" aria-hidden="true">
        <div className="auth-layout__brand-inner">
          <div className="auth-layout__logo">
            <CBCLogoIcon />
            <span className="auth-layout__logo-text">CBC Learn</span>
          </div>
          <div className="auth-layout__brand-content">
            <h1 className="auth-layout__tagline">
              Uganda's Digital Learning Platform
            </h1>
            <p className="auth-layout__subtitle">
              Aligned with the Competency-Based Curriculum. Learn anywhere.
              Grow every day.
            </p>
          </div>
          <div className="auth-layout__brand-dots" aria-hidden />
        </div>
      </div>

      {/* ── Right / Form Panel ─────────────────────────────────────────────── */}
      <div className="auth-layout__form-panel">
        <div className="auth-layout__form-container">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

function CBCLogoIcon() {
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="CBC Learn logo"
    >
      <rect width="40" height="40" rx="10" fill="white" fillOpacity="0.15" />
      <path
        d="M12 20C12 15.582 15.582 12 20 12C22.21 12 24.21 12.895 25.657 14.343"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M28 20C28 24.418 24.418 28 20 28C17.79 28 15.79 27.105 14.343 25.657"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="20" cy="20" r="3" fill="white" />
    </svg>
  );
}
