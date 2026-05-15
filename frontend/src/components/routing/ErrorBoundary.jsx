/**
 * ErrorBoundary.jsx
 *
 * Wraps route subtrees so that a thrown error in any child component
 * shows a graceful fallback instead of unmounting the entire app.
 *
 * Usage (router/index.jsx):
 *   <ErrorBoundary>
 *     <AppLayout />
 *   </ErrorBoundary>
 */

import { Component } from "react";

// ── Fallback UI ───────────────────────────────────────────────────────────────
function ErrorFallback({ error, onRetry }) {
  return (
    <div className="error-boundary" role="alert" aria-live="assertive">
      <div className="error-boundary__card">
        <div className="error-boundary__icon" aria-hidden>⚠️</div>
        <h2 className="error-boundary__title">Something went wrong</h2>
        <p className="error-boundary__message">
          {error?.message || "An unexpected error occurred."}
        </p>
        <div className="error-boundary__actions">
          <button
            className="btn btn-primary btn-md"
            onClick={onRetry}
          >
            Try again
          </button>
          <button
            className="btn btn-secondary btn-md"
            onClick={() => window.location.assign("/")}
          >
            Go to home
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Boundary ──────────────────────────────────────────────────────────────────
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // In production this would send to a logging service (e.g. Sentry)
    console.error("[ErrorBoundary] Caught error:", error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.handleRetry}
        />
      );
    }
    return this.props.children;
  }
}
