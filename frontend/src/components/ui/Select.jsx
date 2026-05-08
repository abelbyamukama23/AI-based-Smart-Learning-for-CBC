/**
 * Select.jsx — Reusable Select with label and error state
 */

import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export const Select = forwardRef(function Select(
  { label, id, error, helperText, className, required, children, ...props },
  ref
) {
  return (
    <div className="form-field">
      {label && (
        <label htmlFor={id} className="form-label">
          {label}
          {required && <span className="form-required">*</span>}
        </label>
      )}
      <select
        id={id}
        ref={ref}
        className={cn("form-select", error && "form-input--error", className)}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      >
        {children}
      </select>
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
