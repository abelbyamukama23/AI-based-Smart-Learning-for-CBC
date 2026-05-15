import PropTypes from "prop-types";

/**
 * Skeleton — Generic loading placeholder (SOLID: Single Responsibility)
 * Replaces duplicated skeleton loaders across dashboards and pages.
 * Open/Closed: Accepts `className` and `style` to be styled flexibly by parent without modification.
 */
export function Skeleton({ className = "", style = {} }) {
  return <div className={`skeleton ${className}`} style={style} aria-hidden="true" />;
}

Skeleton.propTypes = {
  className: PropTypes.string,
  style: PropTypes.object,
};
