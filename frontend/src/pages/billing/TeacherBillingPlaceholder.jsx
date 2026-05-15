import styles from "./TeacherBilling.module.css";
import { IconBilling } from "../../components/Icons";

export default function TeacherBillingPlaceholder() {
  return (
    <div className={styles["billing-container"]}>
      <div className={styles["billing-card"]}>
        <div className={styles["billing-icon-ring"]}>
          <IconBilling size={40} />
        </div>

        <h1 className={styles["billing-title"]}>Billing & Subscriptions</h1>
        <p className={styles["billing-desc"]}>
          We are building a comprehensive billing dashboard for teachers and institutions.
          Soon, you'll be able to manage subscriptions, purchase AI token bundles for your
          classrooms, and view detailed invoice history.
        </p>

        <div className={styles["billing-features"]}>
          {[
            { icon: "💳", label: "Manage Subscriptions" },
            { icon: "🪙", label: "Token Top-ups" },
            { icon: "📊", label: "Usage Analytics" },
            { icon: "🧾", label: "Invoice History" },
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
