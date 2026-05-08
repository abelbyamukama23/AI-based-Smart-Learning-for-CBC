/**
 * LessonsPage.jsx — Browse and search all CBC lessons
 *
 * Backend: GET /api/v1/curriculum/lessons/
 *   Filter: ?subject=<id>&class_level=<id>&search=<text>
 *   Pagination: ?page=<n>
 */

import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getLessons, getSubjects, getClassLevels } from "../../services/curriculum.service";
import useAuthStore from "../../store/authStore";

function Skeleton({ className }) {
  return <div className={`skeleton ${className || ""}`} />;
}

function LessonCard({ lesson }) {
  return (
    <Link
      to={`/learner/lessons/${lesson.id}`}
      className="lesson-card"
      aria-label={`Open lesson: ${lesson.title}`}
    >
      <div className="lesson-card__subject-badge">{lesson.subject_name || "Lesson"}</div>
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

export default function LessonsPage() {
  const user = useAuthStore((s) => s.user);

  const [lessons, setLessons]       = useState([]);
  const [subjects, setSubjects]     = useState([]);
  const [levels, setLevels]         = useState([]);
  const [loading, setLoading]       = useState(true);
  const [page, setPage]             = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext]       = useState(false);

  // Filters
  const [search, setSearch]         = useState("");
  const [subjectFilter, setSubject] = useState("");
  const [levelFilter, setLevel]     = useState("");

  // Load filters metadata once
  useEffect(() => {
    Promise.allSettled([getSubjects(), getClassLevels()]).then(([s, l]) => {
      if (s.status === "fulfilled") setSubjects(s.value.results ?? s.value);
      if (l.status === "fulfilled") setLevels(l.value.results ?? l.value);
    });
  }, []);

  // Load lessons when filters/page change (debounced for search)
  const fetchLessons = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (subjectFilter) params.subject = subjectFilter;
      if (levelFilter) params.class_level = levelFilter;

      const data = await getLessons(params);
      setLessons(data.results ?? data);
      setTotalCount(data.count ?? (data.results ?? data).length);
      setHasNext(!!data.next);
    } finally {
      setLoading(false);
    }
  }, [page, search, subjectFilter, levelFilter]);

  useEffect(() => {
    const t = setTimeout(fetchLessons, search ? 400 : 0);
    return () => clearTimeout(t);
  }, [fetchLessons]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleFilter = (setter) => (e) => {
    setter(e.target.value);
    setPage(1);
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1 className="page-header__title">📖 Lessons</h1>
        <p className="page-header__subtitle">
          Browse CBC-aligned lessons for your curriculum level.
        </p>
      </div>

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <div className="filter-bar">
        <div className="filter-bar__search">
          <span className="filter-bar__icon" aria-hidden>🔍</span>
          <input
            id="lesson-search"
            type="search"
            className="filter-bar__input"
            placeholder="Search lessons…"
            value={search}
            onChange={handleSearchChange}
            aria-label="Search lessons"
          />
        </div>

        <select
          id="lesson-subject-filter"
          className="filter-bar__select"
          value={subjectFilter}
          onChange={handleFilter(setSubject)}
          aria-label="Filter by subject"
        >
          <option value="">All Subjects</option>
          {subjects.map(s => (
            <option key={s.id} value={s.id}>{s.subject_name}</option>
          ))}
        </select>

        <select
          id="lesson-level-filter"
          className="filter-bar__select"
          value={levelFilter}
          onChange={handleFilter(setLevel)}
          aria-label="Filter by class level"
        >
          <option value="">All Levels</option>
          {levels.map(l => (
            <option key={l.id} value={l.id}>{l.level_name}</option>
          ))}
        </select>
      </div>

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {!loading && (
        <p className="results-count">
          {totalCount > 0 ? `${totalCount} lesson${totalCount !== 1 ? "s" : ""} found` : "No lessons found"}
        </p>
      )}

      <div className="lesson-grid lesson-grid--wide">
        {loading
          ? [1,2,3,4,5,6].map(i => <Skeleton key={i} className="skeleton--card" />)
          : lessons.length === 0
          ? (
            <div className="empty-state empty-state--full">
              <span className="empty-state__icon">📭</span>
              <p className="empty-state__msg">No lessons match your filters. Try adjusting the search.</p>
            </div>
          )
          : lessons.map(l => <LessonCard key={l.id} lesson={l} />)
        }
      </div>

      {/* ── Pagination ──────────────────────────────────────────────────── */}
      {(hasNext || page > 1) && (
        <div className="pagination">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ← Previous
          </button>
          <span className="pagination__info">Page {page}</span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setPage(p => p + 1)}
            disabled={!hasNext}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
