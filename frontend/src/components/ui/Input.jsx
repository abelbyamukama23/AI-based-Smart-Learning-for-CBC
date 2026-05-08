/**
 * Input.jsx — Reusable Input with label, error, and helper text
 */

import { forwardRef, useState } from "react";
import { cn } from "../../lib/utils";

export const Input = forwardRef(function Input(
  {
    label,
    id,
    type = "text",
    error,
    helperText,
    className,
    required,
    ...props
  },
  ref
) {
  const isPassword = type === "password";
  const [showPassword, setShowPassword] = useState(false);
  const inputType = isPassword ? (showPassword ? "text" : "password") : type;

  return (
    <div className="form-field">
      {label && (
        <label htmlFor={id} className="form-label">
          {label}
          {required && <span className="form-required">*</span>}
        </label>
      )}
      <div className={cn("input-wrapper", isPassword && "input-wrapper--password")}>
        <input
          id={id}
          ref={ref}
          type={inputType}
          className={cn("form-input", error && "form-input--error", className)}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            className="input-password-toggle"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        )}
      </div>
      {error && (
        <p id={`${id}-error`} className="form-error" role="alert">
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={`${id}-helper`} className="form-helper">
          {helperText}
        </p>
      )}
    </div>
  );
});
