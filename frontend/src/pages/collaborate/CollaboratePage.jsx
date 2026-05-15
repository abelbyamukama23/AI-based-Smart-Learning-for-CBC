import styles from "./CollaboratePage.module.css";

export default function CollaboratePage() {
  return (
    <div className={styles["collaborate-container"]}>
      <div className={styles["collaborate-card"]}>
        <div className={styles["collaborate-icon-ring"]}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>

        <h1 className={styles["collaborate-title"]}>Collaboration Hub</h1>
        <p className={styles["collaborate-desc"]}>
          Study groups, peer reviews, and shared learning spaces are on their way.
          Learners will soon be able to form groups, share notes, and challenge
          each other with quizzes — all powered by Mwalimu AI.
        </p>

        <div className={styles["collaborate-features"]}>
          {[
            { icon: "👥", label: "Study Groups" },
            { icon: "📝", label: "Shared Notes" },
            { icon: "🏆", label: "Peer Challenges" },
            { icon: "💬", label: "Group Chat" },
          ].map((f) => (
            <div key={f.label} className={styles["feature-chip"]}>
              <span>{f.icon}</span>
              <span>{f.label}</span>
            </div>
          ))}
        </div>

        <div className={styles["coming-soon-badge"]}>
          <span className={styles["badge-dot"]} />
          Coming Soon
        </div>
      </div>
    </div>
  );
}
