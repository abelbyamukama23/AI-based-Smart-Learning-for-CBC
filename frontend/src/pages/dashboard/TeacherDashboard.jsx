/**
 * TeacherDashboard.jsx — Home dashboard for teacher role
 *
 * Sections:
 *  - Welcome banner
 *  - Quick stats
 *  - Recent lessons
 *  - Recent feed posts
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import { getLessons, getSubjects } from "../../services/curriculum.service";
import { getFeedPosts } from "../../services/feed.service";
import { getProfile } from "../../services/auth.service";

function Skeleton({ className }) {
  return <div className={`skeleton ${className || ""}`} />;
}

function StatCard({ icon, label, value, loading, color }) {
  return (
    <div className={`stat-card stat-card--${color}`}>
      <div className="stat-card__icon" aria-hidden>{icon}</div>
      <div className="stat-card__body">
        <span className="stat-card__label">{label}</span>
        {loading ? (
          <Skeleton className="skeleton--sm" />
        ) : (
          <span className="stat-card__value">{value ?? "—"}</span>
        )}
      </div>
    </div>
  );
}

function LessonCard({ lesson }) {
  return (
    <Link
      to={`/teacher/lessons/${lesson.id}`}
      className="lesson-card"
      aria-label={`Open lesson: ${lesson.title}`}
    >
      <div className="lesson-card__subject-badge">{lesson.subject_name || "Subject"}</div>
      <h3 className="lesson-card__title">{lesson.title}</h3>
      <p className="lesson-card__desc">{lesson.description?.slice(0, 100)}…</p>
      <div className="lesson-card__meta">
        <span className="lesson-card__level">{lesson.class_level_name || "—"}</span>
        {lesson.is_downloadable && (
          <span className="lesson-card__badge lesson-card__badge--dl">⬇ Downloadable</span>
        )}
      </div>
    </Link>
  );
}

function FeedPostPreview({ post }) {
  return (
    <div className="feed-preview-card">
      <div className="feed-preview-card__author">
        <div className="feed-preview-card__avatar">
          {post.author_detail?.username?.[0]?.toUpperCase() || "U"}
        </div>
        <div>
          <span className="feed-preview-card__name">
            {post.author_detail?.username || "Learner"}
          </span>
          <span className="feed-preview-card__time">
            {new Date(post.date_posted).toLocaleDateString()}
          </span>
        </div>
      </div>
      <p className="feed-preview-card__content">{post.content?.slice(0, 120)}{post.content?.length > 120 ? "…" : ""}</p>
      <div className="feed-preview-card__stats">
        <span>❤️ {post.reaction_count}</span>
        <span>💬 {post.comment_count}</span>
      </div>
    </div>
  );
}

export default function TeacherDashboard() {
  const user = useAuthStore((s) => s.user);

  const [profile, setProfile] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [feedPosts, setFeedPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [profileData, subjectsData, lessonsData, feedData] =
          await Promise.allSettled([
            getProfile(),
            getSubjects(),
            getLessons({ page_size: 6 }),
            getFeedPosts({ page: 1 }),
          ]);

        if (profileData.status === "fulfilled") setProfile(profileData.value);
        if (subjectsData.status === "fulfilled") setSubjects(subjectsData.value.results ?? subjectsData.value);
        if (lessonsData.status === "fulfilled") setLessons(lessonsData.value.results ?? []);
        if (feedData.status === "fulfilled") setFeedPosts((feedData.value.results ?? []).slice(0, 3));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const displayName =
    profile?.first_name
      ? `${profile.first_name}${profile.last_name ? " " + profile.last_name : ""}`
      : user?.email?.split("@")[0] || "Teacher";

  return (
    <div className="dashboard">
      {/* ── Welcome banner ─────────────────────────────────────────────── */}
      <div className="welcome-banner">
        <div className="welcome-banner__text">
          <h1 className="welcome-banner__title">
            Welcome back, <span>{displayName}</span> 👋
          </h1>
          <p className="welcome-banner__subtitle">
            CBC Digital Learning Platform • Teacher Portal
          </p>
        </div>
        <Link to="/teacher/lessons" className="welcome-banner__cta">
          <span>Browse Curriculum</span>
          <span aria-hidden>📚</span>
        </Link>
      </div>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className="stats-row">
        <StatCard icon="📚" label="Subjects" value={subjects.length} loading={loading} color="indigo" />
        <StatCard icon="📖" label="Total Lessons" value={lessons.length > 0 ? `${lessons.length}+` : "—"} loading={loading} color="teal" />
        <StatCard icon="💬" label="Recent Activity" value={feedPosts.length > 0 ? `${feedPosts.length}+` : "—"} loading={loading} color="amber" />
      </div>

      {/* ── Two column grid ─────────────────────────────────────────────── */}
      <div className="dashboard__grid">
        {/* Left — Recent Lessons */}
        <section className="dashboard__section">
          <div className="section-header">
            <h2 className="section-header__title">Curriculum Updates</h2>
            <Link to="/teacher/lessons" className="section-header__link">View all →</Link>
          </div>

          {loading ? (
            <div className="lesson-grid">
              {[1,2,3].map(i => <Skeleton key={i} className="skeleton--card" />)}
            </div>
          ) : lessons.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state__icon" aria-hidden>📖</span>
              <p className="empty-state__msg">No lessons available yet.</p>
            </div>
          ) : (
            <div className="lesson-grid">
              {lessons.slice(0, 3).map((l) => (
                <LessonCard key={l.id} lesson={l} />
              ))}
            </div>
          )}
        </section>

        {/* Right — Feed */}
        <div className="dashboard__sidebar-col">
          <section className="dashboard__section">
            <div className="section-header">
              <h2 className="section-header__title">Learner Feed</h2>
              <Link to="/teacher/feed" className="section-header__link">See all →</Link>
            </div>
            {loading ? (
              [1,2].map(i => <Skeleton key={i} className="skeleton--feed" />)
            ) : feedPosts.length === 0 ? (
              <div className="empty-state">
                <span className="empty-state__icon" aria-hidden>💬</span>
                <p className="empty-state__msg">No learner activity to display.</p>
              </div>
            ) : (
              feedPosts.map(p => <FeedPostPreview key={p.id} post={p} />)
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
