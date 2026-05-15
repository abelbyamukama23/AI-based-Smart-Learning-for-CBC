import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import styles from "./LessonCard.module.css";

/**
 * Helper to determine cover gradient based on subject name
 */
function getCoverClass(subjectName = "") {
  const name = subjectName.toLowerCase();
  if (name.includes("math")) return styles["lessonCover--math"];
  if (name.includes("sci") || name.includes("bio") || name.includes("phy")) return styles["lessonCover--science"];
  if (name.includes("eng") || name.includes("lit") || name.includes("lang")) return styles["lessonCover--language"];
  if (name.includes("hist") || name.includes("geo")) return styles["lessonCover--history"];
  return styles["lessonCover--default"];
}

export function LessonCard({ lesson, showProgress, progressValue, rolePath }) {
  const isDownloadable = lesson.is_downloadable;

  return (
    <Link
      to={`/${rolePath}/lessons/${lesson.id}`}
      className={styles.lessonCard}
      aria-label={`Open lesson: ${lesson.title}`}
    >
      <div className={`${styles.lessonCover} ${getCoverClass(lesson.subject_name)}`}>
        <div className={styles.lessonBadge}>{lesson.subject_name || "Subject"}</div>
      </div>
      
      <div className={styles.lessonBody}>
        <h3 className={styles.lessonTitle}>{lesson.title}</h3>
        <p className={styles.lessonDesc}>{lesson.description}</p>
        
        {showProgress && (
          <div className={styles.progressContainer}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progressValue || 0}%` }} />
            </div>
            <span className={styles.progressText}>{progressValue || 0}% Complete</span>
          </div>
        )}

        <div className={styles.lessonMeta}>
          <span className={styles.lessonLevel}>{lesson.class_level_name || "—"}</span>
          <div className={styles.lessonTags}>
            {isDownloadable && (
              <span className={`${styles.lessonTag} ${styles["lessonTag--dl"]}`}>
                ⬇ DL
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

LessonCard.propTypes = {
  lesson: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    subject_name: PropTypes.string,
    class_level_name: PropTypes.string,
    is_downloadable: PropTypes.bool,
  }).isRequired,
  showProgress: PropTypes.bool,
  progressValue: PropTypes.number,
  rolePath: PropTypes.oneOf(["learner", "teacher"]),
};

LessonCard.defaultProps = {
  showProgress: false,
  progressValue: 0,
  rolePath: "learner",
};
