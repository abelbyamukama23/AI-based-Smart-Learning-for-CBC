/**
 * LessonDetailPage.jsx — Full lesson detail view
 *
 * Backend: GET /api/v1/curriculum/lessons/{id}/
 * Returns: LessonDetailSerializer — includes body_html, competencies, video_url, image
 */

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getLessonDetail } from "../../services/curriculum.service";

function Skeleton({ className }) {
  return <div className={`skeleton ${className || ""}`} />;
}

export default function LessonDetailPage() {
  const { id } = useParams();
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getLessonDetail(id)
      .then(setLesson)
      .catch(() => setError("Lesson not found or unavailable."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="dashboard">
        <Skeleton className="skeleton--title" />
        <Skeleton className="skeleton--body" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="empty-state">
          <span className="empty-state__icon">⚠️</span>
          <p className="empty-state__msg">{error}</p>
          <Link to="/learner/lessons" className="btn btn-ghost btn-sm">← Back to Lessons</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard lesson-detail">
      {/* Breadcrumb */}
      <nav className="breadcrumb" aria-label="Navigation breadcrumb">
        <Link to="/learner/dashboard" className="breadcrumb__item">Dashboard</Link>
        <span className="breadcrumb__sep" aria-hidden>›</span>
        <Link to="/learner/lessons" className="breadcrumb__item">Lessons</Link>
        <span className="breadcrumb__sep" aria-hidden>›</span>
        <span className="breadcrumb__item breadcrumb__item--active">{lesson.title}</span>
      </nav>

      {/* Header */}
      <div className="lesson-detail__header">
        <div className="lesson-detail__badges">
          <span className="lesson-card__subject-badge">{lesson.subject_name || "Subject"}</span>
          <span className="lesson-card__level">{lesson.class_level_name || "—"}</span>
          {lesson.is_downloadable && (
            <span className="lesson-card__badge lesson-card__badge--dl">⬇ Downloadable</span>
          )}
        </div>
        <h1 className="lesson-detail__title">{lesson.title}</h1>
        <p className="lesson-detail__desc">{lesson.description}</p>
        <div className="lesson-detail__meta">
          <span>Source: {lesson.source}</span>
          {lesson.file_size_kb && <span>Size: {lesson.file_size_kb} KB</span>}
        </div>
      </div>

      {/* Video */}
      {lesson.video_url && (
        <div className="lesson-detail__video">
          <iframe
            src={lesson.video_url}
            title={`Video for ${lesson.title}`}
            allowFullScreen
            loading="lazy"
          />
        </div>
      )}

      {/* Image */}
      {lesson.image && (
        <img
          className="lesson-detail__image"
          src={lesson.image}
          alt={lesson.title}
          loading="lazy"
        />
      )}

      {/* Body HTML */}
      {lesson.body_html && (
        <div
          className="lesson-detail__body prose"
          dangerouslySetInnerHTML={{ __html: lesson.body_html }}
        />
      )}

      {/* Competencies */}
      {lesson.competencies?.length > 0 && (
        <div className="lesson-detail__competencies">
          <h2>Competencies Covered</h2>
          <ul>
            {lesson.competencies.map(c => (
              <li key={c.id}>
                <strong>{c.competency_name}</strong>
                {c.description && <p>{c.description}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Link to="/learner/lessons" className="btn btn-ghost btn-sm">← Back to Lessons</Link>
    </div>
  );
}
