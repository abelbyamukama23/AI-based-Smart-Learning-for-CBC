/**
 * FeedPage.jsx — Knowledge Feed
 *
 * Backend:
 *   GET    /api/v1/feed/posts/               → paginated posts
 *   POST   /api/v1/feed/posts/               → create post { content, visibility }
 *   POST   /api/v1/feed/posts/{id}/react/    → { type: "LIKE" }
 *   GET    /api/v1/feed/posts/{id}/comments/ → comments
 *   POST   /api/v1/feed/posts/{id}/comments/ → { text }
 *   DELETE /api/v1/feed/posts/{id}/          → soft delete (author only)
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFeedPosts, createPost, reactToPost, deletePost, getComments, addComment } from "../../services/feed.service";
import { extractApiError } from "../../lib/utils";
import useAuthStore from "../../store/authStore";
import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatRelative } from "../../lib/dateUtils";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import styles from "./FeedPage.module.css";

function Avatar({ name }) {
  return (
    <div className={styles["feed-avatar"]} aria-hidden>
      {name?.[0]?.toUpperCase() || "U"}
    </div>
  );
}

// ── Create Post Form ──────────────────────────────────────────────────────────
function CreatePostForm({ onCreated }) {
  const user = useAuthStore((s) => s.user);
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState("PEERS");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const post = await createPost({ content: content.trim(), visibility });
      setContent("");
      onCreated(post);
    } catch (err) {
      setError(extractApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className={styles["create-post-form"]} onSubmit={handleSubmit} aria-label="Create a post">
      <div className={styles["create-post-form__header"]}>
        <Avatar name={user?.first_name || user?.email} />
        <textarea
          id="new-post-content"
          className={styles["create-post-form__input"]}
          placeholder="Share something with your peers…"
          value={content}
          onChange={e => setContent(e.target.value)}
          rows={3}
          aria-label="Post content"
          disabled={submitting}
        />
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className={styles["create-post-form__footer"]}>
        <select
          id="post-visibility"
          className={`form-select ${styles["create-post-form__visibility"]}`}
          value={visibility}
          onChange={e => setVisibility(e.target.value)}
          aria-label="Post visibility"
        >
          <option value="PEERS">👥 Peers</option>
          <option value="PUBLIC">🌐 Public</option>
          <option value="PRIVATE">🔒 Private</option>
          <option value="TEACHERS">🏫 Teachers</option>
        </select>
        <button
          type="submit"
          className="btn btn-primary btn-sm"
          disabled={submitting || !content.trim()}
        >
          {submitting ? "Posting…" : "Post"}
        </button>
      </div>
    </form>
  );
}

// ── Comment section ───────────────────────────────────────────────────────────
function CommentsSection({ postId }) {
  const [text, setText] = useState("");
  const queryClient = useQueryClient();

  const { data: comments = [], isLoading: loading } = useQuery({
    queryKey: ["comments", postId],
    queryFn: () => getComments(postId).then(data => Array.isArray(data) ? data : (data.results ?? [])),
  });

  const { mutate: submitComment, isPending: posting } = useMutation({
    mutationFn: (newText) => addComment(postId, newText),
    onSuccess: () => {
      setText("");
      queryClient.invalidateQueries({ queryKey: ["comments", postId] });
    }
  });

  const submit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    submitComment(text.trim());
  };

  return (
    <div className={styles["comments-section"]}>
      {loading ? (
        <p className={styles["comments-section__loading"]}>Loading comments…</p>
      ) : comments.length === 0 ? (
        <p className={styles["comments-section__empty"]}>No comments yet.</p>
      ) : (
        <ul className={styles["comments-section__list"]}>
          {comments.map(c => (
            <li key={c.id} className={styles["comment"]}>
              <Avatar name={c.author_detail?.username} />
              <div className={styles["comment__body"]}>
                <span className={styles["comment__author"]}>{c.author_detail?.username || "User"}</span>
                <p className={styles["comment__text"]}>{c.text}</p>
                <span className={styles["comment__time"]}>{formatRelative(c.date_posted)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
      <form className={styles["comment-form"]} onSubmit={submit}>
        <input
          type="text"
          className={`form-input ${styles["comment-form__input"]}`}
          placeholder="Add a comment…"
          value={text}
          onChange={e => setText(e.target.value)}
          disabled={posting}
          aria-label="Write a comment"
        />
        <button type="submit" className="btn btn-secondary btn-sm" disabled={posting || !text.trim()}>
          Reply
        </button>
      </form>
    </div>
  );
}

// ── Post card ─────────────────────────────────────────────────────────────────
export function PostCard({ post, currentUserId, onDelete }) {
  const navigate = useNavigate();
  const [reactionCount, setReactionCount] = useState(post.reaction_count ?? 0);
  const [showComments, setShowComments]   = useState(false);
  const [reacting, setReacting]           = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);  // ← replaces window.confirm

  const isAuthor = post.author === currentUserId || post.author_detail?.id === currentUserId;

  const handleReact = async () => {
    setReacting(true);
    try {
      const res = await reactToPost(post.id, "LIKE");
      setReactionCount(prev => res.action === "liked" ? prev + 1 : Math.max(0, prev - 1));
    } finally {
      setReacting(false);
    }
  };

  const handleDeleteConfirmed = async () => {
    await deletePost(post.id);
    onDelete(post.id);
  };


  return (
    <article className={styles["post-card"]} aria-label={`Post by ${post.author_detail?.username}`}>
      {/* Header */}
      <div className={styles["post-card__header"]}>
        <Avatar name={post.author_detail?.username || post.author_detail?.email} />
        <div className={styles["post-card__author-info"]}>
          <span className={styles["post-card__author-name"]}>
            {post.author_detail?.username || "Learner"}
          </span>
          <span className={styles["post-card__time"]}>{formatRelative(post.date_posted)}</span>
        </div>
        <span className={`${styles["visibility-badge"]} ${styles[`visibility-badge--${post.visibility?.toLowerCase()}`] || ""}`}>
          {visibilityIcon(post.visibility)} {post.visibility}
        </span>
        {isAuthor && (
          confirmDelete ? (
            <div className={styles["post-card__confirm-row"]}>
              <span className={styles["post-card__confirm-label"]}>Delete post?</span>
              <button
                className="btn btn-danger btn-sm"
                onClick={handleDeleteConfirmed}
                aria-label="Confirm delete post"
              >
                Delete
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setConfirmDelete(false)}
                aria-label="Cancel delete"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              className={styles["post-card__delete"]}
              onClick={() => setConfirmDelete(true)}
              aria-label="Delete post"
              title="Delete post"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
              </svg>
            </button>
          )
        )}
      </div>

      {/* Content */}
      <p className={styles["post-card__content"]}>{post.content}</p>

      {/* Media */}
      {post.photo && (
        <img className={styles["post-card__photo"]} src={post.photo} alt="Post photo" loading="lazy" />
      )}

      {/* Actions */}
      <div className={styles["post-card__actions"]}>
        <button
          className={styles["post-action"]}
          onClick={handleReact}
          disabled={reacting}
          aria-label={`Like post. ${reactionCount} likes`}
        >
          ❤️ <span>{reactionCount}</span>
        </button>
        <button
          className={styles["post-action"]}
          onClick={() => setShowComments(p => !p)}
          aria-expanded={showComments}
          aria-label={`Comments. ${post.comment_count} comments`}
        >
          💬 <span>{post.comment_count ?? 0}</span>
        </button>
        <button
          className={styles["post-action"]}
          onClick={() => navigate(`/learner/feed/${post.id}`, { state: { autoAskMwalimu: true }})}
          aria-label="Ask Mwalimu about this post"
        >
          🤖 <span>Ask Mwalimu</span>
        </button>
      </div>

      {/* Comments */}
      {showComments && <CommentsSection postId={post.id} />}
    </article>
  );
}

function visibilityIcon(v) {
  const m = { PUBLIC: "🌐", PEERS: "👥", PRIVATE: "🔒", TEACHERS: "🏫" };
  return m[v] || "";
}

// ── FeedPage ──────────────────────────────────────────────────────────────────
export default function FeedPage() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();

  const {
    data,
    isLoading: loading,
    isFetchingNextPage,
    hasNextPage: hasNext,
    fetchNextPage
  } = useInfiniteQuery({
    queryKey: ["feedPosts"],
    queryFn: ({ pageParam = 1 }) => getFeedPosts({ page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => lastPage.next ? allPages.length + 1 : undefined,
  });

  const posts = data?.pages.flatMap(page => page.results ?? page) ?? [];

  const handleCreated = () => {
    queryClient.invalidateQueries({ queryKey: ["feedPosts"] });
  };

  const handleDelete = () => {
    queryClient.invalidateQueries({ queryKey: ["feedPosts"] });
  };

  const loadMore = () => {
    if (hasNext) fetchNextPage();
  };


  return (
    <div className="dashboard">
      <div className="page-header">
        <h1 className="page-header__title">💬 Knowledge Feed</h1>
        <p className="page-header__subtitle">Share insights, ask peers, build knowledge together.</p>
      </div>

      <div className={styles["feed-layout"]}>
        {/* Create post */}
        <CreatePostForm onCreated={handleCreated} />

        {/* Posts */}
        {loading && posts.length === 0 ? (
          <div className={styles["feed-loading"]}>
            {[1,2,3].map(i => <Skeleton key={i} className="skeleton--feed" />)}
          </div>
        ) : posts.length === 0 ? (
          <EmptyState icon="💬" message="No posts yet. Be the first to share!" />
        ) : (
          <>
            {posts.map(post => (
              <PostCard
                key={post.id}
                post={post}
                currentUserId={user?.user_id || user?.id}
                onDelete={handleDelete}
              />
            ))}
            {hasNext && (
              <button
                className="btn btn-ghost btn-md load-more"
                onClick={loadMore}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Loading…" : "Load more"}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
