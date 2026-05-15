/**
 * LibraryPage.jsx — CBC Curriculum Library Browser
 *
 * Learners can:
 *  • Browse all uploaded curriculum materials (PDFs, maps, audio, images)
 *  • Filter by subject, class level, file type
 *  • Search by keyword
 *  • Click "Read with Mwalimu" to open the tutor with the material as context
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getLibraryFiles, getSubjects, getLevels } from "../../services/library.service";
import useAuthStore from "../../store/authStore";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "../../hooks/useDebounce";
import { IconLibrary, IconSearch, IconChevronDown } from "../../components/Icons";
import styles from "./LibraryPage.module.css";

// ── File type config ──────────────────────────────────────────────────────────
const FILE_TYPE_META = {
  PDF:   { label: "Textbook",      icon: "📄", color: "#e74c3c", bg: "#fdf2f2" },
  IMAGE: { label: "Illustration",  icon: "🖼",  color: "#9b59b6", bg: "#f8f4fd" },
  AUDIO: { label: "Audio",         icon: "🎧", color: "#27ae60", bg: "#f2faf5" },
  MAP:   { label: "Map",           icon: "🗺",  color: "#2980b9", bg: "#f2f8fe" },
  VIDEO: { label: "Video",         icon: "🎬", color: "#f39c12", bg: "#fef9f0" },
  OTHER: { label: "Resource",      icon: "📎", color: "#7f8c8d", bg: "#f5f5f5" },
};

function getTypeMeta(type) {
  return FILE_TYPE_META[type] || FILE_TYPE_META.OTHER;
}

// ─────────────────────────────────────────────────────────────────────────────
export default function LibraryPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const role = user?.role?.toLowerCase() === "teacher" ? "teacher" : "learner";

  const [filters, setFilters] = useState({
    search:       "",
    subject_name: "",
    level_name:   "",
    type:         "",
  });


  // ── Load filter options on mount ──────────────────────────────────────────
  const { data: subjects = [] } = useQuery({
    queryKey: ["subjects", "library"],
    queryFn: getSubjects,
    staleTime: Infinity,
  });

  const { data: levels = [] } = useQuery({
    queryKey: ["levels", "library"],
    queryFn: getLevels,
    staleTime: Infinity,
  });

  const debouncedSearch = useDebounce(filters.search, 350);

  // ── Fetch files whenever filters change ───────────────────────────────────
  const { data: filesData, isLoading: loading, isError, refetch: fetchFiles } = useQuery({
    queryKey: ["libraryFiles", { ...filters, search: debouncedSearch }],
    queryFn: () => getLibraryFiles({ ...filters, search: debouncedSearch }),
  });

  const files = filesData ?? [];
  const error = isError ? "Could not load library. Please try again." : null;

  const handleFilterChange = (key, value) =>
    setFilters((prev) => ({ ...prev, [key]: value }));

  const handleReadWithMwalimu = (file) => {
    navigate(`/${role}/tutor`, {
      state: { libraryFile: file },
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className={styles["library-page"]}>
      {/* ── Header ───────────────────────────────────────────────────────── */}
      <div className={styles["library-header"]}>
        <div className={styles["library-header__text"]}>
          <h1 className={styles["library-header__title"]}>
            <span className={styles["library-header__icon"]}><IconLibrary size={36} /></span>
            CBC Library
          </h1>
          <p className={styles["library-header__subtitle"]}>
            Browse textbooks, maps, and study materials from the Uganda
            Competence-Based Curriculum. Open any resource and Mwalimu will
            guide you through it.
          </p>
        </div>
        <div className={styles["library-header__stats"]}>
          <span className={styles["library-stat"]}>
            <strong>{files.length}</strong> resources
          </span>
        </div>
      </div>

      {/* ── Filter bar ───────────────────────────────────────────────────── */}
      <div className={styles["library-filters"]}>
        {/* Search */}
        <div className={styles["library-search"]}>
          <span className={styles["library-search__icon"]}><IconSearch size={18} /></span>
          <input
            id="library-search-input"
            type="search"
            placeholder="Search textbooks, maps, topics..."
            value={filters.search}
            onChange={(e) => handleFilterChange("search", e.target.value)}
            className={styles["library-search__input"]}
          />
          {filters.search && (
            <button
              className={styles["library-search__clear"]}
              onClick={() => handleFilterChange("search", "")}
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className={styles["library-filters__divider"]} />

        {/* Subject */}
        <div className={styles["library-select-wrapper"]}>
          <select
            id="library-subject-filter"
            className={styles["library-select"]}
            value={filters.subject_name}
            onChange={(e) => handleFilterChange("subject_name", e.target.value)}
          >
            <option value="">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.subject_name}>
                {s.subject_name}
              </option>
            ))}
          </select>
          <span className={styles["library-select-icon"]}><IconChevronDown size={16} /></span>
        </div>

        <div className={styles["library-filters__divider"]} />

        {/* Level */}
        <div className={styles["library-select-wrapper"]}>
          <select
            id="library-level-filter"
            className={styles["library-select"]}
            value={filters.level_name}
            onChange={(e) => handleFilterChange("level_name", e.target.value)}
          >
            <option value="">All Levels</option>
            {levels.map((l) => (
              <option key={l.id} value={l.level_name}>
                {l.level_name}
              </option>
            ))}
          </select>
          <span className={styles["library-select-icon"]}><IconChevronDown size={16} /></span>
        </div>

        <div className={styles["library-filters__divider"]} />

        {/* Type */}
        <div className={styles["library-select-wrapper"]}>
          <select
            id="library-type-filter"
            className={styles["library-select"]}
            value={filters.type}
            onChange={(e) => handleFilterChange("type", e.target.value)}
          >
            <option value="">All Types</option>
            {Object.entries(FILE_TYPE_META).map(([key, meta]) => (
              <option key={key} value={key}>
                {meta.icon} {meta.label}
              </option>
            ))}
          </select>
          <span className={styles["library-select-icon"]}><IconChevronDown size={16} /></span>
        </div>

        {/* Clear all */}
        {Object.values(filters).some(Boolean) && (
          <button
            id="library-clear-filters"
            className={styles["library-clear-btn"]}
            onClick={() =>
              setFilters({ search: "", subject_name: "", level_name: "", type: "" })
            }
          >
            Clear Filters
          </button>
        )}
      </div>


      {/* ── Content ──────────────────────────────────────────────────────── */}
      {loading ? (
        <LibraryLoading />
      ) : error ? (
        <LibraryError message={error} onRetry={fetchFiles} />
      ) : files.length === 0 ? (
        <LibraryEmpty />
      ) : (
        <div className={styles["library-grid"]}>
          {files.map((file) => (
            <LibraryCard
              key={file.id}
              file={file}
              onReadWithMwalimu={handleReadWithMwalimu}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Library Card ──────────────────────────────────────────────────────────────
function LibraryCard({ file, onReadWithMwalimu }) {
  const meta = getTypeMeta(file.file_type);
  const tags = file.tag_list?.slice(0, 3) ?? [];

  return (
    <article className={styles["library-card"]} style={{ "--card-accent": meta.color }}>
      {/* Type badge */}
      <div className={styles["library-card__type-badge"]} style={{ background: meta.bg, color: meta.color }}>
        <span className={styles["library-card__type-icon"]}>{meta.icon}</span>
        <span className={styles["library-card__type-label"]}>{meta.label}</span>
      </div>

      {/* Content */}
      <div className={styles["library-card__body"]}>
        <h2 className={styles["library-card__title"]}>{file.title}</h2>
        {file.description && (
          <p className={styles["library-card__desc"]}>{file.description}</p>
        )}

        {/* Meta row */}
        <div className={styles["library-card__meta"]}>
          {file.subject_name && (
            <span className={`${styles["library-card__meta-pill"]} ${styles["library-card__meta-pill--subject"]}`}>
              {file.subject_name}
            </span>
          )}
          {file.class_level_name && (
            <span className={`${styles["library-card__meta-pill"]} ${styles["library-card__meta-pill--level"]}`}>
              {file.class_level_name}
            </span>
          )}
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className={styles["library-card__tags"]}>
            {tags.map((tag) => (
              <span key={tag} className={styles["library-card__tag"]}>
                #{tag}
              </span>
            ))}
          </div>
        )}

        {file.source && (
          <p className={styles["library-card__source"]}>Source: {file.source}</p>
        )}
      </div>

      {/* Actions */}
      <div className={styles["library-card__actions"]}>
        <button
          id={`mwalimu-btn-${file.id}`}
          className={`${styles["library-card__btn"]} ${styles["library-card__btn--primary"]}`}
          onClick={() => onReadWithMwalimu(file)}
        >
          <span>🤖</span>
          Read with Mwalimu
        </button>
        {file.file_url && (
          <a
            href={file.file_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`${styles["library-card__btn"]} ${styles["library-card__btn--secondary"]}`}
          >
            <span>⬇</span>
            Open File
          </a>
        )}
      </div>

      {/* RAG indexed indicator */}
      {file.is_indexed && (
        <div className={styles["library-card__indexed-badge"]} title="This resource has been indexed for Mwalimu search">
          AI Ready
        </div>
      )}
    </article>
  );
}

// ── States ────────────────────────────────────────────────────────────────────
function LibraryLoading() {
  return (
    <div className={styles["library-grid"]}>
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className={`${styles["library-card"]} ${styles["library-card--skeleton"]}`}>
          <div className="skeleton skeleton--badge" />
          <div className="skeleton skeleton--title" />
          <div className="skeleton skeleton--text" />
          <div className="skeleton skeleton--text skeleton--short" />
        </div>
      ))}
    </div>
  );
}

function LibraryEmpty() {
  return (
    <div className={styles["library-empty"]}>
      <div className={styles["library-empty__icon"]}>📭</div>
      <h3 className={styles["library-empty__title"]}>No resources found</h3>
      <p className={styles["library-empty__text"]}>
        Try adjusting your filters or search terms. More curriculum materials are
        added regularly by the admin and Mwalimu's Research Agent.
      </p>
    </div>
  );
}

function LibraryError({ message, onRetry }) {
  return (
    <div className={styles["library-error"]}>
      <div className={styles["library-error__icon"]}>⚠️</div>
      <p>{message}</p>
      <button className={`${styles["library-card__btn"]} ${styles["library-card__btn--primary"]}`} onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}
