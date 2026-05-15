import styles from "./BillingPages.module.css";

const USAGE_DATA = [
  { label: "Mon", sessions: 4, queries: 22 },
  { label: "Tue", sessions: 6, queries: 35 },
  { label: "Wed", sessions: 2, queries: 11 },
  { label: "Thu", sessions: 8, queries: 47 },
  { label: "Fri", sessions: 5, queries: 28 },
  { label: "Sat", sessions: 3, queries: 14 },
  { label: "Sun", sessions: 1, queries: 6 },
];

const MAX_QUERIES = Math.max(...USAGE_DATA.map(d => d.queries));

export default function UsagePage() {
  const totalSessions = USAGE_DATA.reduce((s, d) => s + d.sessions, 0);
  const totalQueries  = USAGE_DATA.reduce((s, d) => s + d.queries, 0);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Usage</h1>
          <p className={styles.subtitle}>Your Mwalimu AI activity for the last 7 days.</p>
        </div>
      </header>

      {/* Stats */}
      <div className={styles["stats-row"]}>
        <div className={styles["stat-card"]}>
          <span className={styles["stat-value"]}>{totalSessions}</span>
          <span className={styles["stat-label"]}>Sessions this week</span>
        </div>
        <div className={styles["stat-card"]}>
          <span className={styles["stat-value"]}>{totalQueries}</span>
          <span className={styles["stat-label"]}>Questions asked</span>
        </div>
        <div className={styles["stat-card"]}>
          <span className={styles["stat-value"]}>{(totalQueries / 7).toFixed(1)}</span>
          <span className={styles["stat-label"]}>Avg. questions/day</span>
        </div>
      </div>

      {/* Bar chart */}
      <div className={styles["chart-card"]}>
        <h2 className={styles["chart-title"]}>Daily Questions Asked</h2>
        <div className={styles["bar-chart"]}>
          {USAGE_DATA.map((d) => (
            <div key={d.label} className={styles["bar-group"]}>
              <div className={styles["bar-wrap"]}>
                <span className={styles["bar-value"]}>{d.queries}</span>
                <div
                  className={styles.bar}
                  style={{ height: `${(d.queries / MAX_QUERIES) * 140}px` }}
                />
              </div>
              <span className={styles["bar-label"]}>{d.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
