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
import { getChatThreads } from "../../services/tutor.service";
import { getProfile } from "../../services/auth.service";
import { IconLibrary, IconBook, IconBot, IconChat, MwalimuLogo } from "../../components/Icons";

import { Skeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { EmptyState } from "../../components/ui/EmptyState";
import { LessonCard } from "../../components/shared/LessonCard";
import { FeedPostPreview } from "../../components/shared/FeedPostPreview";
import styles from "./Dashboard.module.css";

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
            getChatThreads(),
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

  // Helper to determine greeting based on time
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className={styles.dashboard}>
      {/* ── Welcome banner ─────────────────────────────────────────────── */}
      <div className={styles.welcomeBanner}>
        <div className={styles.welcomeText}>
          <span className={styles.welcomeGreeting}>{getGreeting()}</span>
          <h1 className={styles.welcomeTitle}>
            Welcome back, <span>{displayName}</span> 👋
          </h1>
          <p className={styles.welcomeSubtitle}>
            {classLevel
              ? `${classLevel} · CBC Digital Learning Platform`
              : "CBC Digital Learning Platform"}
          </p>
        </div>
        <Link to="/learner/tutor" className={styles.welcomeCta}>
          <span>Ask Mwalimu</span>
          <IconSparkle />
        </Link>
      </div>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className={styles.statsRow}>
        <StatCard icon={<IconLibrary size={24} />} label="Subjects Available" value={subjects.length} loading={loading} color="indigo" trend="up" trendValue="+2 New" />
        <StatCard icon={<IconBook size={24} />} label="Lessons" value={lessons.length > 0 ? `${lessons.length}+` : "—"} loading={loading} color="teal" />
        <StatCard icon={<IconBot size={24} />} label="AI Sessions" value={aiCount} loading={loading} color="violet" trend="up" trendValue="+15%" />
        <StatCard icon={<IconChat size={24} />} label="Feed Posts" value={feedPosts.length > 0 ? `${feedPosts.length}+` : "—"} loading={loading} color="amber" />
      </div>

      {/* ── Two column grid ─────────────────────────────────────────────── */}
      <div className={styles.dashboardGrid}>
        {/* Left — Recent Lessons */}
        <section className={styles.dashboardSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Recent Lessons</h2>
            <Link to="/learner/lessons" className={styles.sectionLink}>View all →</Link>
          </div>

          {loading ? (
            <div className="lesson-grid">
              {[1,2,3].map(i => <Skeleton key={i} className="skeleton--card" />)}
            </div>
          ) : lessons.length === 0 ? (
            <EmptyState icon={<IconBook size={32} />} message="No lessons available yet. Check back soon." />
          ) : (
            <div className="lesson-grid">
              {lessons.slice(0, 3).map((l, index) => (
                <LessonCard key={l.id} lesson={l} showProgress={true} progressValue={35 + index * 25} rolePath="learner" />
              ))}
            </div>
          )}
        </section>

        {/* Right — Feed + AI CTA */}
        <div className={styles.sidebarCol}>
          {/* Premium AI Tutor CTA card */}
          <div className={styles.aiCtaCard}>
            <div className={styles.aiIconWrapper} aria-hidden>
              <MwalimuLogo size={56} />
            </div>
            <div className={styles.aiTextWrapper}>
              <h3 className={styles.aiTitle}>Ask Mwalimu</h3>
              <p className={styles.aiDesc}>
                Get instant, curriculum-aligned answers and master your subjects.
              </p>
            </div>
            <Link to="/learner/tutor" className={styles.aiBtn}>
              Start AI Session
            </Link>
          </div>

          {/* Feed snippet */}
          <section className={styles.dashboardSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Knowledge Feed</h2>
              <Link to="/learner/feed" className={styles.sectionLink}>See all →</Link>
            </div>
            {loading ? (
              [1,2].map(i => <Skeleton key={i} className="skeleton--feed" />)
            ) : feedPosts.length === 0 ? (
              <EmptyState icon={<IconChat size={32} />} message="No posts yet. Be the first to share!" />
            ) : (
              feedPosts.map(p => <FeedPostPreview key={p.id} post={p} />)
            )}
          </section>
        </div>
      </div>
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
