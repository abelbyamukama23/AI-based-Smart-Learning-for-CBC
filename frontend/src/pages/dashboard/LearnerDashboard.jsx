/**
 * LearnerDashboard.jsx — Home dashboard for learner role
 *
 * Sections:
 *  - Welcome banner (name, class_level from profile)
 *  - Quick stats (subjects count, recent lessons, AI sessions)
 *  - Recent lessons (from /curriculum/lessons/?class_level=...)
 *  - Start AI Tutor CTA
 *  - Recent feed posts
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import { getLessons, getSubjects } from "../../services/curriculum.service";
import { getFeedPosts } from "../../services/feed.service";
import { getTutorHistory } from "../../services/tutor.service";
import { getProfile } from "../../services/auth.service";

// ── Skeleton loader ───────────────────────────────────────────────────────────
function Skeleton({ className }) {
  return <div className={`skeleton ${className || ""}`} />;
}

// ── Stat card ─────────────────────────────────────────────────────────────────
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

// ── Lesson card ───────────────────────────────────────────────────────────────
function LessonCard({ lesson }) {
  return (
    <Link
      to={`/learner/lessons/${lesson.id}`}
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

// ── Feed post preview ─────────────────────────────────────────────────────────
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
            {formatRelative(post.date_posted)}
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

// ── Main component ────────────────────────────────────────────────────────────
export default function LearnerDashboard() {
  const user = useAuthStore((s) => s.user);

  const [profile, setProfile] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [feedPosts, setFeedPosts] = useState([]);
  const [aiCount, setAiCount] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [profileData, subjectsData, lessonsData, feedData, aiData] =
          await Promise.allSettled([
            getProfile(),
            getSubjects(),
            getLessons({ page_size: 6 }),
            getFeedPosts({ page: 1 }),
            getTutorHistory(),
          ]);

        if (profileData.status === "fulfilled") setProfile(profileData.value);
        if (subjectsData.status === "fulfilled") setSubjects(subjectsData.value.results ?? subjectsData.value);
        if (lessonsData.status === "fulfilled") setLessons(lessonsData.value.results ?? []);
        if (feedData.status === "fulfilled") setFeedPosts((feedData.value.results ?? []).slice(0, 3));
        if (aiData.status === "fulfilled") setAiCount(Array.isArray(aiData.value) ? aiData.value.length : (aiData.value.count ?? 0));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const displayName =
    profile?.first_name
      ? `${profile.first_name}${profile.last_name ? " " + profile.last_name : ""}`
      : user?.email?.split("@")[0] || "Learner";

  const classLevel = profile?.learner_profile?.class_level || user?.class_level;

  return (
    <div className="dashboard">
      {/* ── Welcome banner ─────────────────────────────────────────────── */}
      <div className="welcome-banner">
        <div className="welcome-banner__text">
          <h1 className="welcome-banner__title">
            Welcome back, <span>{displayName}</span> 👋
          </h1>
          <p className="welcome-banner__subtitle">
            {classLevel
              ? `${classLevel} · CBC Digital Learning Platform`
              : "CBC Digital Learning Platform"}
          </p>
        </div>
        <Link to="/learner/tutor" className="welcome-banner__cta">
          <span>Ask Mwalimu</span>
          <IconSparkle />
        </Link>
      </div>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className="stats-row">
        <StatCard icon="📚" label="Subjects Available" value={subjects.length} loading={loading} color="indigo" />
        <StatCard icon="📖" label="Lessons" value={lessons.length > 0 ? `${lessons.length}+` : "—"} loading={loading} color="teal" />
        <StatCard icon="🤖" label="AI Sessions" value={aiCount} loading={loading} color="violet" />
        <StatCard icon="💬" label="Feed Posts" value={feedPosts.length > 0 ? `${feedPosts.length}+` : "—"} loading={loading} color="amber" />
      </div>

      {/* ── Two column grid ─────────────────────────────────────────────── */}
      <div className="dashboard__grid">
        {/* Left — Recent Lessons */}
        <section className="dashboard__section">
          <div className="section-header">
            <h2 className="section-header__title">Recent Lessons</h2>
            <Link to="/learner/lessons" className="section-header__link">View all →</Link>
          </div>

          {loading ? (
            <div className="lesson-grid">
              {[1,2,3].map(i => <Skeleton key={i} className="skeleton--card" />)}
            </div>
          ) : lessons.length === 0 ? (
            <EmptyState icon="📖" message="No lessons available yet. Check back soon." />
          ) : (
            <div className="lesson-grid">
              {lessons.slice(0, 3).map((l) => (
                <LessonCard key={l.id} lesson={l} />
              ))}
            </div>
          )}
        </section>

        {/* Right — Feed + AI CTA */}
        <div className="dashboard__sidebar-col">
          {/* AI Tutor CTA card */}
          <div className="ai-cta-card">
            <div className="ai-cta-card__icon" aria-hidden>🤖</div>
            <div>
              <h3 className="ai-cta-card__title">Mwalimu</h3>
              <p className="ai-cta-card__desc">
                Get instant, curriculum-aligned answers to your questions.
              </p>
            </div>
            <Link to="/learner/tutor" className="btn btn-primary btn-sm ai-cta-card__btn">
              Start Chat
            </Link>
          </div>

          {/* Feed snippet */}
          <section className="dashboard__section">
            <div className="section-header">
              <h2 className="section-header__title">Knowledge Feed</h2>
              <Link to="/learner/feed" className="section-header__link">See all →</Link>
            </div>
            {loading ? (
              [1,2].map(i => <Skeleton key={i} className="skeleton--feed" />)
            ) : feedPosts.length === 0 ? (
              <EmptyState icon="💬" message="No posts yet. Be the first to share!" />
            ) : (
              feedPosts.map(p => <FeedPostPreview key={p.id} post={p} />)
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function EmptyState({ icon, message }) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon" aria-hidden>{icon}</span>
      <p className="empty-state__msg">{message}</p>
    </div>
  );
}

function IconSparkle() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function formatRelative(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
