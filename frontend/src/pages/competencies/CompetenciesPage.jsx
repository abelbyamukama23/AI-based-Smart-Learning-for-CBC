import styles from "./CompetenciesPage.module.css";

const SAMPLE_COMPETENCIES = [
  { subject: "Mathematics", competency: "Solve quadratic equations", level: "S4", status: "achieved" },
  { subject: "Biology",     competency: "Explain cell division (mitosis & meiosis)", level: "S4", status: "achieved" },
  { subject: "Chemistry",   competency: "Balance chemical equations",  level: "S4", status: "in-progress" },
  { subject: "Geography",   competency: "Analyse physical features of East Africa", level: "S4", status: "in-progress" },
  { subject: "English",     competency: "Write a formal argumentative essay", level: "S4", status: "not-started" },
];

const STATUS_META = {
  "achieved":    { label: "Achieved",     color: "#15803d", bg: "#f0fdf4", border: "#bbf7d0", dot: "#22c55e" },
  "in-progress": { label: "In Progress",  color: "#92400e", bg: "#fffbeb", border: "#fde68a", dot: "#f59e0b" },
  "not-started": { label: "Not Started",  color: "#6b7280", bg: "#f9fafb", border: "#e5e7eb", dot: "#9ca3af" },
};

export default function CompetenciesPage() {
  const achieved    = SAMPLE_COMPETENCIES.filter(c => c.status === "achieved").length;
  const total       = SAMPLE_COMPETENCIES.length;
  const pct         = Math.round((achieved / total) * 100);

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>My Competencies</h1>
          <p className={styles.subtitle}>Track your mastery of Uganda CBC learning outcomes.</p>
        </div>
        <div className={styles["progress-pill"]}>
          <svg width="36" height="36" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15" fill="none" stroke="#e5e7eb" strokeWidth="3"/>
            <circle
              cx="18" cy="18" r="15" fill="none"
              stroke="#4f46e5" strokeWidth="3" strokeLinecap="round"
              strokeDasharray={`${pct * 0.94} 94`}
              transform="rotate(-90 18 18)"
            />
          </svg>
          <div>
            <span className={styles["progress-pct"]}>{pct}%</span>
            <span className={styles["progress-label"]}>{achieved}/{total} achieved</span>
          </div>
        </div>
      </header>

      {/* Cards */}
      <div className={styles.grid}>
        {SAMPLE_COMPETENCIES.map((c, i) => {
          const meta = STATUS_META[c.status];
          return (
            <div key={i} className={styles.card}>
              <div className={styles["card-top"]}>
                <span className={styles.subject}>{c.subject}</span>
                <span
                  className={styles["status-badge"]}
                  style={{ color: meta.color, background: meta.bg, border: `1px solid ${meta.border}` }}
                >
                  <span className={styles.dot} style={{ background: meta.dot }} />
                  {meta.label}
                </span>
              </div>
              <p className={styles.competency}>{c.competency}</p>
              <span className={styles["class-tag"]}>{c.level}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
