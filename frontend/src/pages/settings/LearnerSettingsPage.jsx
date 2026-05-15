import { useState, useMemo } from "react";
import { updateProfile } from "../../services/auth.service";
import useAuthStore from "../../store/authStore";
import styles from "./SettingsPage.module.css";
import { IconSettings, IconUser, IconBook } from "../../components/Icons";

export default function LearnerSettingsPage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);

  // Derive stable initial state from store — avoids setState-in-effect anti-pattern
  const defaultFormData = useMemo(() => ({
    preferred_methodology: user?.learner_profile?.preferred_methodology ?? "SOCRATIC",
    preferred_language: user?.learner_profile?.preferred_language ?? "EN",
    familiar_region: user?.learner_profile?.familiar_region ?? "",
    theme: user?.learner_profile?.theme ?? "SYSTEM",
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), []);

  const [formData, setFormData] = useState(defaultFormData);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      const updatedUser = await updateProfile({
        learner_profile: formData,
      });
      setUser(updatedUser);
      setMessage({ type: "success", text: "Settings saved successfully!" });
      
      // Update document theme if changed
      if (formData.theme === "DARK") document.documentElement.classList.add("dark");
      else if (formData.theme === "LIGHT") document.documentElement.classList.remove("dark");
    } catch {
      setMessage({ type: "error", text: "Failed to save settings. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles["settings-container"]}>
      <header className={styles["settings-header"]}>
        <div className={styles["settings-title-wrapper"]}>
          <IconSettings size={28} className={styles["settings-icon"]} />
          <h1 className={styles["settings-title"]}>Preferences & Pedagogy</h1>
        </div>
        <p className={styles["settings-subtitle"]}>
          Customize how Mwalimu AI teaches you based on your unique learning style and background.
        </p>
      </header>

      <form onSubmit={handleSubmit} className={styles["settings-form"]}>
        {/* Methodologies */}
        <section className={styles["settings-section"]}>
          <div className={styles["section-header"]}>
            <IconBook size={20} />
            <h2>Teaching Methodology</h2>
          </div>
          <p className={styles["section-desc"]}>How do you want Mwalimu to explain concepts?</p>
          <div className={styles["form-group"]}>
            <select
              name="preferred_methodology"
              value={formData.preferred_methodology}
              onChange={handleChange}
              className="form-select"
            >
              <option value="SOCRATIC">Socratic (Guides you with questions)</option>
              <option value="DIRECT">Direct Instruction (Straight to the point)</option>
              <option value="VISUAL">Visual & Storytelling (Uses analogies & stories)</option>
              <option value="PROJECT">Project-Based (Focuses on practical application)</option>
            </select>
          </div>
        </section>

        {/* Language & Context */}
        <section className={styles["settings-section"]}>
          <div className={styles["section-header"]}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>
            <h2>Language &amp; Context</h2>
          </div>
          <p className={styles["section-desc"]}>
            Mwalimu defaults to English but can translate key explanations and use localized examples.
          </p>
          <div className={styles["form-row"]}>
            <div className={styles["form-group"]}>
              <label className="form-label">Preferred Translation Language</label>
              <select
                name="preferred_language"
                value={formData.preferred_language}
                onChange={handleChange}
                className="form-select"
              >
                <option value="EN">English (Default)</option>
                <option value="LG">Luganda</option>
                <option value="SW">Swahili</option>
                <option value="RN">Runyankole</option>
              </select>
            </div>
            
            <div className={styles["form-group"]}>
              <label className="form-label">Familiar Region (for local examples)</label>
              <select
                name="familiar_region"
                value={formData.familiar_region}
                onChange={handleChange}
                className="form-select"
              >
                <option value="">None (General Uganda context)</option>
                <option value="Central/Kampala">Central / Kampala</option>
                <option value="Western/Ankole">Western / Ankole</option>
                <option value="Northern/Gulu">Northern / Gulu</option>
                <option value="Eastern/Busoga">Eastern / Busoga</option>
                <option value="West Nile">West Nile</option>
              </select>
            </div>
          </div>
        </section>

        {/* UI Theme */}
        <section className={styles["settings-section"]}>
          <div className={styles["section-header"]}>
            <IconUser size={20} />
            <h2>App Appearance</h2>
          </div>
          <div className={styles["form-group"]}>
            <select
              name="theme"
              value={formData.theme}
              onChange={handleChange}
              className="form-select"
            >
              <option value="SYSTEM">System Default</option>
              <option value="LIGHT">Light Theme</option>
              <option value="DARK">Dark Theme</option>
            </select>
          </div>
        </section>

        {/* Actions */}
        <div className={styles["settings-actions"]}>
          {message.text && (
            <span className={message.type === "success" ? styles["msg-success"] : styles["msg-error"]}>
              {message.type === "success" && (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{marginRight:"6px",verticalAlign:"middle"}}>
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              )}
              {message.text}
            </span>
          )}
          <button type="submit" className={styles["save-btn"]} disabled={loading}>
            {loading ? (
              <>
                <svg className={styles["save-btn__spinner"]} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                  <polyline points="17 21 17 13 7 13 7 21"/>
                  <polyline points="7 3 7 8 15 8"/>
                </svg>
                Save Preferences
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
