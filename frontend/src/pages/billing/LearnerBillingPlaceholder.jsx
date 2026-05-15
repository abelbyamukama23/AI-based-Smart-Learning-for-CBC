import styles from "./TeacherBilling.module.css";
import { IconBilling } from "../../components/Icons";

export default function LearnerBillingPlaceholder() {
  return (
    <div className={styles["billing-container"]}>
      <div className={styles["billing-card"]}>
        <div className={styles["billing-icon-ring"]}>
          <IconBilling size={40} />
        </div>

        <h1 className={styles["billing-title"]}>Billing & Subscriptions</h1>
        <p className={styles["billing-desc"]}>
          We are preparing a centralized billing hub for learners and their guardians.
          Soon, you'll be able to manage your tier (Individual or Institutional), review your 
          invoice history, and upgrade your subscription directly from here.
        </p>

        <div className={styles["billing-features"]}>
          {[
            { icon: "🎓", label: "Manage Tiers" },
            { icon: "🪙", label: "Buy Tokens" },
            { icon: "🛡️", label: "Guardian Access" },
            { icon: "🧾", label: "Payment History" },
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
