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
import { IconLibrary, IconBook, IconChat } from "../../components/Icons";

import { Skeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { EmptyState } from "../../components/ui/EmptyState";
import { LessonCard } from "../../components/shared/LessonCard";
import { FeedPostPreview } from "../../components/shared/FeedPostPreview";
import styles from "./Dashboard.module.css";

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
            Here's what's happening in your digital classroom today.
          </p>
        </div>
      </div>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className={styles.statsRow}>
        <StatCard icon={<IconLibrary size={24} />} label="Total Classes" value={profile?.teacher_profile?.classes?.length || 0} loading={loading} color="indigo" />
        <StatCard icon={<IconBook size={24} />} label="Curriculum Subjects" value={subjects.length > 0 ? subjects.length : "—"} loading={loading} color="teal" />
        <StatCard icon={<IconBook size={24} />} label="Lessons Created" value={lessons.length > 0 ? `${lessons.length}+` : "—"} loading={loading} color="violet" trend="up" trendValue="1 New" />
        <StatCard icon={<IconChat size={24} />} label="Student Discussions" value={feedPosts.length > 0 ? `${feedPosts.length}+` : "—"} loading={loading} color="amber" trend="up" trendValue="+5%" />
      </div>

      {/* ── Two column grid ─────────────────────────────────────────────── */}
      <div className={styles.dashboardGrid}>
        {/* Left — Recent Lessons */}
        <section className={styles.dashboardSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Recent Lessons</h2>
            <Link to="/teacher/lessons" className={styles.sectionLink}>Manage all →</Link>
          </div>

          {loading ? (
            <div className="lesson-grid">
              {[1,2,3].map(i => <Skeleton key={i} className="skeleton--card" />)}
            </div>
          ) : lessons.length === 0 ? (
            <EmptyState icon={<IconBook size={32} />} message="No lessons available yet." />
          ) : (
            <div className="lesson-grid">
              {lessons.slice(0, 3).map((l) => (
                <LessonCard key={l.id} lesson={l} rolePath="teacher" />
              ))}
            </div>
          )}
        </section>

        {/* Right — Activity Feed */}
        <div className={styles.sidebarCol}>
          <section className={styles.dashboardSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Learner Activity</h2>
              <Link to="/teacher/feed" className={styles.sectionLink}>See all →</Link>
            </div>
            {loading ? (
              [1,2].map(i => <Skeleton key={i} className="skeleton--feed" />)
            ) : feedPosts.length === 0 ? (
              <EmptyState icon={<IconChat size={32} />} message="No learner activity to display." />
            ) : (
              feedPosts.map(p => <FeedPostPreview key={p.id} post={p} />)
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
