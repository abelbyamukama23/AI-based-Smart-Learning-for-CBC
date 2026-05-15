import PropTypes from "prop-types";

/**
 * EmptyState — Generic placeholder for empty lists (SOLID: Single Responsibility)
 * Replaces duplicated empty states across dashboards and pages.
 * Open/Closed: Can pass any `icon` node and `message` string.
 */
export function EmptyState({ icon, message, className = "" }) {
  return (
    <div className={`empty-state ${className}`}>
      {icon && (
        <span className="empty-state__icon" aria-hidden="true">
          {icon}
        </span>
      )}
      <p className="empty-state__msg">{message}</p>
    </div>
  );
}

EmptyState.propTypes = {
  icon: PropTypes.node,
  message: PropTypes.string.isRequired,
  className: PropTypes.string,
};
