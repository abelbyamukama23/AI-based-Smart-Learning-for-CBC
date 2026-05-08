/**
 * AlertBanner.jsx — Inline alert for top-level form errors
 */

import { cn } from "../../lib/utils";

const icons = {
  error: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M10 6v4M10 14h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  success: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M6.5 10.5l2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  info: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M10 9v6M10 7h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
};

export function AlertBanner({ message, type = "error", className }) {
  if (!message) return null;
  return (
    <div
      className={cn("alert-banner", `alert-banner--${type}`, className)}
      role="alert"
      aria-live="polite"
    >
      <span className="alert-banner__icon">{icons[type]}</span>
      <span className="alert-banner__message">{message}</span>
    </div>
  );
}
