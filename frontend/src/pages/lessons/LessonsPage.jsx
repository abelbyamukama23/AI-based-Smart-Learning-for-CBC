/**
 * LessonsPage.jsx — Browse and search all CBC lessons
 *
 * Backend: GET /api/v1/curriculum/lessons/
 *   Filter: ?subject=<id>&class_level=<id>&search=<text>
 *   Pagination: ?page=<n>
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { getLessons, getSubjects, getClassLevels } from "../../services/curriculum.service";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "../../hooks/useDebounce";
import { IconSearch, IconChevronDown, IconBook } from "../../components/Icons";
import styles from "./LessonsPage.module.css";

import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { LessonCard } from "../../components/shared/LessonCard";

export default function LessonsPage() {
  const [page, setPage]             = useState(1);
  const [search, setSearch]         = useState("");
  const [subjectFilter, setSubject] = useState("");
  const [levelFilter, setLevel]     = useState("");

  const debouncedSearch = useDebounce(search, 400);

  // Load filters metadata once (cached infinitely)
  const { data: subjects = [] } = useQuery({
    queryKey: ["subjects"],
    queryFn: () => getSubjects().then(res => res.results ?? res),
    staleTime: Infinity,
  });

  const { data: levels = [] } = useQuery({
    queryKey: ["levels"],
    queryFn: () => getClassLevels().then(res => res.results ?? res),
    staleTime: Infinity,
  });

  // Load lessons when filters/page change
  const { data: lessonsData, isLoading: loading } = useQuery({
    queryKey: ["lessons", { page, search: debouncedSearch, subject: subjectFilter, class_level: levelFilter }],
    queryFn: () => {
      const params = { page };
      if (debouncedSearch) params.search = debouncedSearch;
      if (subjectFilter) params.subject = subjectFilter;
      if (levelFilter) params.class_level = levelFilter;
      return getLessons(params);
    },
  });

  const lessons = lessonsData?.results ?? (Array.isArray(lessonsData) ? lessonsData : []);
  const totalCount = lessonsData?.count ?? lessons.length;
  const hasNext = !!lessonsData?.next;


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
      <div className={styles["page-header"]}>
        <h1 className={styles["page-header__title"]}><IconBook size={28} /> Lessons</h1>
        <p className={styles["page-header__subtitle"]}>
          Browse CBC-aligned lessons for your curriculum level.
        </p>
      </div>

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <div className={styles["filter-bar"]}>
        <div className={styles["filter-bar__search"]}>
          <span className={styles["filter-bar__icon"]} aria-hidden><IconSearch size={18} /></span>
          <input
            id="lesson-search"
            type="search"
            className={styles["filter-bar__input"]}
            placeholder="Search lessons…"
            value={search}
            onChange={handleSearchChange}
            aria-label="Search lessons"
          />
          {search && (
            <button
              className={styles["filter-bar__search-clear"]}
              onClick={() => {
                setSearch("");
                setPage(1);
              }}
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className={styles["filter-bar__divider"]} />

        <div className={styles["filter-bar__select-wrapper"]}>
          <select
            id="lesson-subject-filter"
            className={styles["filter-bar__select"]}
            value={subjectFilter}
            onChange={handleFilter(setSubject)}
            aria-label="Filter by subject"
          >
            <option value="">All Subjects</option>
            {subjects.map(s => (
              <option key={s.id} value={s.id}>{s.subject_name}</option>
            ))}
          </select>
          <span className={styles["filter-bar__select-icon"]}><IconChevronDown size={16} /></span>
        </div>

        <div className={styles["filter-bar__divider"]} />

        <div className={styles["filter-bar__select-wrapper"]}>
          <select
            id="lesson-level-filter"
            className={styles["filter-bar__select"]}
            value={levelFilter}
            onChange={handleFilter(setLevel)}
            aria-label="Filter by class level"
          >
            <option value="">All Levels</option>
            {levels.map(l => (
              <option key={l.id} value={l.id}>{l.level_name}</option>
            ))}
          </select>
          <span className={styles["filter-bar__select-icon"]}><IconChevronDown size={16} /></span>
        </div>
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
            <EmptyState className="empty-state--full" icon={<IconBook size={32} />} message="No lessons match your filters. Try adjusting the search." />
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
