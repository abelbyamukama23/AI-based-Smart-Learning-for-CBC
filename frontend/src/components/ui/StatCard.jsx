import PropTypes from "prop-types";
import { Skeleton } from "./Skeleton";
import styles from "./StatCard.module.css";

export function StatCard({ icon, label, value, loading, color, trend, trendValue }) {
  const getTrendClass = () => {
    if (trend === "up") return styles.trendUp;
    if (trend === "down") return styles.trendDown;
    return styles.trendNeutral;
  };

  const getTrendIcon = () => {
    if (trend === "up") return "↑";
    if (trend === "down") return "↓";
    return "−";
  };

  return (
    <div className={`${styles.statCard} ${styles[`statCard--${color}`]}`}>
      <div className={styles.statCardTop}>
        <div className={styles.statCardIcon} aria-hidden>{icon}</div>
        {trendValue && (
          <div className={`${styles.statTrend} ${getTrendClass()}`}>
            <span>{getTrendIcon()}</span>
            <span>{trendValue}</span>
          </div>
        )}
      </div>
      <div className={styles.statBody}>
        <span className={styles.statLabel}>{label}</span>
        {loading ? (
          <Skeleton className="skeleton--sm" />
        ) : (
          <span className={styles.statValue}>{value ?? "—"}</span>
        )}
      </div>
    </div>
  );
}

StatCard.propTypes = {
  icon: PropTypes.node.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  loading: PropTypes.bool,
  color: PropTypes.oneOf(["indigo", "teal", "violet", "amber", "rose"]),
  trend: PropTypes.oneOf(["up", "down", "neutral"]),
  trendValue: PropTypes.string,
};

StatCard.defaultProps = {
  color: "indigo",
  loading: false,
};
