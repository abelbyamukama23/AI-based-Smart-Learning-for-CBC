import styles from "./BillingPages.module.css";

const PLAN = { name: "Student Free", tokens: 500, used: 317 };
const pct = Math.round((PLAN.used / PLAN.tokens) * 100);
const barColor = pct >= 90 ? "#ef4444" : pct >= 70 ? "#f59e0b" : "#4f46e5";

const HISTORY = [
  { date: "May 15", action: "Tutor session — Biology",   cost: 18 },
  { date: "May 15", action: "YouTube research query",     cost: 12 },
  { date: "May 14", action: "Tutor session — Mathematics",cost: 22 },
  { date: "May 14", action: "SVG diagram generation",     cost: 8  },
  { date: "May 13", action: "Tutor session — Chemistry",  cost: 15 },
];

export default function TokensPage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Tokens</h1>
          <p className={styles.subtitle}>Monitor your AI token balance and consumption history.</p>
        </div>
      </header>

      {/* Balance card */}
      <div className={styles["balance-card"]}>
        <div className={styles["balance-top"]}>
          <div>
            <span className={styles["balance-plan"]}>{PLAN.name} Plan</span>
            <p className={styles["balance-numbers"]}>
              <strong>{PLAN.tokens - PLAN.used}</strong>
              <span> tokens remaining of {PLAN.tokens}</span>
            </p>
          </div>
          <span className={styles["balance-pct"]} style={{ color: barColor }}>{pct}%</span>
        </div>
        {/* Progress bar */}
        <div className={styles["token-bar-bg"]}>
          <div
            className={styles["token-bar-fill"]}
            style={{ width: `${pct}%`, background: barColor }}
          />
        </div>
        {pct >= 80 && (
          <p className={styles["token-warning"]}>
            ⚠️ You are running low on tokens. Upgrade your plan to continue uninterrupted.
          </p>
        )}
      </div>

      {/* History table */}
      <div className={styles["table-card"]}>
        <h2 className={styles["chart-title"]}>Recent Token Usage</h2>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Date</th>
              <th>Action</th>
              <th>Tokens Used</th>
            </tr>
          </thead>
          <tbody>
            {HISTORY.map((row, i) => (
              <tr key={i}>
                <td>{row.date}</td>
                <td>{row.action}</td>
                <td>
                  <span className={styles["token-chip"]}>−{row.cost}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
