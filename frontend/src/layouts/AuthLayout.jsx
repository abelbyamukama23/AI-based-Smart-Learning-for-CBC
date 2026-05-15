/**
 * AuthLayout.jsx — Layout wrapper for all authentication pages.
 * Provides the two-panel structure (brand panel + form panel).
 * The actual visual design will be applied after Figma review.
 */

import { Outlet, Link } from "react-router-dom";
import { MwalimuLogo } from "../components/Icons";

export function AuthLayout() {
  return (
    <div className="auth-layout">
      {/* ── Left / Brand Panel ─────────────────────────────────────────────── */}
      <div className="auth-layout__brand" aria-hidden="true">
        <div className="auth-layout__brand-inner">
          <div className="auth-layout__logo">
            <MwalimuLogo size={44} />
            <span className="auth-layout__logo-text">Mwalimu AI</span>
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


