/**
 * Button.jsx — Reusable Button primitive
 */

import { cn } from "../../lib/utils";

const variants = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  danger: "btn-danger",
};

const sizes = {
  sm: "btn-sm",
  md: "btn-md",
  lg: "btn-lg",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  isLoading = false,
  disabled = false,
  type = "button",
  onClick,
  ...props
}) {
  return (
    <button
      type={type}
      className={cn("btn", variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      onClick={onClick}
      {...props}
    >
      {isLoading ? (
        <span className="btn-loading">
          <Spinner size="sm" />
          <span>Loading…</span>
        </span>
      ) : (
        children
      )}
    </button>
  );
}

function Spinner({ size = "sm" }) {
  return (
    <svg
      className={cn("spinner", size === "sm" ? "spinner-sm" : "spinner-md")}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}
