import { useState, useRef, useEffect } from "react";
import { formatDate } from "./helpers";
import { IconCompose, IconSearch, IconPanel, IconSimulate, IconProject, IconExperiment } from "../../../components/Icons";
import styles from "../TutorPage.module.css";

export function ChatSidebar({
  sidebarOpen,
  setSidebarOpen,
  threadsLoading,
  threads,
  activeThreadId,
  startNewChat,
  loadThread,
  searchQuery,
  setSearchQuery,
}) {
  const [isSearching, setIsSearching] = useState(false);
  const searchInputRef = useRef(null);

  useEffect(() => {
    if (isSearching && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isSearching]);
  return (
    <aside
      className={`${styles["tutor-sidebar"]} ${sidebarOpen ? styles["tutor-sidebar--open"] : styles["tutor-sidebar--closed"]}`}
      aria-label="Chat history"
    >
      {/* ── Top bar ─────────────────────────────────────────────────── */}
      <div className={styles["tutor-sidebar__topbar"]}>
        {/* Title */}
        {sidebarOpen && (
          <span className={styles["tutor-sidebar__brand"]}>Chat history</span>
        )}

        {/* Panel toggle — far right */}
        <button
          className={styles["tutor-sidebar__icon-btn"]}
          onClick={() => setSidebarOpen((o) => !o)}
          aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          <IconPanel size={18} />
        </button>
      </div>

      {/* ── Action rows (open state) ─────────────────────────────────── */}
      {sidebarOpen && (
        <nav className={styles["tutor-sidebar__nav"]}>
          {/* New chat */}
          <button
            className={styles["tutor-sidebar__nav-row"]}
            onClick={startNewChat}
            id="new-chat-btn"
          >
            <IconCompose size={18} />
            <span>New chat</span>
          </button>

          {/* Search chats */}
          {!isSearching && !searchQuery ? (
            <button
              className={styles["tutor-sidebar__nav-row"]}
              onClick={() => setIsSearching(true)}
              aria-label="Search chats"
            >
              <IconSearch size={18} />
              <span>Search chats</span>
            </button>
          ) : (
            <div className={`${styles["tutor-sidebar__nav-row"]} ${styles["tutor-sidebar__nav-row--search"]}`}>
              <IconSearch size={18} />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onBlur={() => {
                  if (!searchQuery) setIsSearching(false);
                }}
                placeholder="Search chats..."
                className={styles["tutor-sidebar__search-input"]}
              />
              {searchQuery && (
                <button
                  className={styles["tutor-sidebar__search-clear"]}
                  onClick={() => {
                    setSearchQuery("");
                    searchInputRef.current?.focus();
                  }}
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          {/* Simulate */}
          <button
            className={styles["tutor-sidebar__nav-row"]}
            onClick={() => {/* future: open simulate */}}
            aria-label="Simulate"
          >
            <IconSimulate size={18} />
            <span>Simulate</span>
          </button>

          {/* Start Project */}
          <button
            className={styles["tutor-sidebar__nav-row"]}
            onClick={() => {/* future: open project */}}
            aria-label="Start Project"
          >
            <IconProject size={18} />
            <span>Start Project</span>
          </button>

          {/* Experiments */}
          <button
            className={styles["tutor-sidebar__nav-row"]}
            onClick={() => {/* future: open experiments */}}
            aria-label="Experiments"
          >
            <IconExperiment size={18} />
            <span>Experiments</span>
          </button>
        </nav>
      )}

      {/* ── Action icons (collapsed state) ──────────────────────────── */}
      {!sidebarOpen && (
        <div className={styles["tutor-sidebar__collapsed-actions"]}>
          <button
            className={styles["tutor-sidebar__icon-btn"]}
            onClick={startNewChat}
            aria-label="New chat"
            title="New chat"
          >
            <IconCompose size={18} />
          </button>
          <button
            className={styles["tutor-sidebar__icon-btn"]}
            aria-label="Search chats"
            title="Search chats"
            onClick={() => {
              setSidebarOpen(true);
              setIsSearching(true);
            }}
          >
            <IconSearch size={18} />
          </button>
          <button
            className={styles["tutor-sidebar__icon-btn"]}
            aria-label="Simulate"
            title="Simulate"
          >
            <IconSimulate size={18} />
          </button>
          <button
            className={styles["tutor-sidebar__icon-btn"]}
            aria-label="Start Project"
            title="Start Project"
          >
            <IconProject size={18} />
          </button>
          <button
            className={styles["tutor-sidebar__icon-btn"]}
            aria-label="Experiments"
            title="Experiments"
          >
            <IconExperiment size={18} />
          </button>
        </div>
      )}

      {/* ── Thread history ───────────────────────────────────────────── */}
      {sidebarOpen && (
        <div className={styles["tutor-sidebar__list"]}>
          <p className={styles["tutor-sidebar__title"]}>My Research</p>

          {threadsLoading ? (
            <div className={styles["tutor-threads-skeleton"]} aria-busy="true" aria-label="Loading conversations">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className={styles["tutor-thread-skeleton"]}>
                  <div className={`skeleton ${styles["tutor-thread-skeleton__title"]}`} />
                  <div className={`skeleton ${styles["tutor-thread-skeleton__meta"]}`} />
                </div>
              ))}
            </div>
          ) : threads.length === 0 ? (
            <p className={styles["tutor-sidebar__hint"]}>No conversations yet. Start one!</p>
          ) : (
            threads.map((t) => (
              <button
                key={t.id}
                className={`${styles["tutor-thread-item"]} ${t.id === activeThreadId ? styles["tutor-thread-item--active"] : ""}`}
                onClick={() => loadThread(t.id)}
                id={`thread-${t.id}`}
              >
                <span className={styles["tutor-thread-item__title"]}>{t.title || "Untitled Chat"}</span>
                <span className={styles["tutor-thread-item__meta"]}>
                  {formatDate(t.updated_at)} · {t.interaction_count} {t.interaction_count === 1 ? "turn" : "turns"}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </aside>
  );
}
