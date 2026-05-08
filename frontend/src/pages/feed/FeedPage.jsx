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

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getFeedPosts,
  createPost,
  reactToPost,
  deletePost,
  getComments,
  addComment,
} from "../../services/feed.service";
import { extractApiError } from "../../lib/utils";
import useAuthStore from "../../store/authStore";

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

function Avatar({ name }) {
  return (
    <div className="feed-avatar" aria-hidden>
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
    <form className="create-post-form" onSubmit={handleSubmit} aria-label="Create a post">
      <div className="create-post-form__header">
        <Avatar name={user?.first_name || user?.email} />
        <textarea
          id="new-post-content"
          className="create-post-form__input"
          placeholder="Share something with your peers…"
          value={content}
          onChange={e => setContent(e.target.value)}
          rows={3}
          aria-label="Post content"
          disabled={submitting}
        />
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="create-post-form__footer">
        <select
          id="post-visibility"
          className="form-select create-post-form__visibility"
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
  const [comments, setComments] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [text, setText]         = useState("");
  const [posting, setPosting]   = useState(false);

  useEffect(() => {
    getComments(postId)
      .then(data => setComments(Array.isArray(data) ? data : (data.results ?? [])))
      .finally(() => setLoading(false));
  }, [postId]);

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setPosting(true);
    try {
      const c = await addComment(postId, text.trim());
      setComments(prev => [...prev, c]);
      setText("");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="comments-section">
      {loading ? (
        <p className="comments-section__loading">Loading comments…</p>
      ) : comments.length === 0 ? (
        <p className="comments-section__empty">No comments yet.</p>
      ) : (
        <ul className="comments-section__list">
          {comments.map(c => (
            <li key={c.id} className="comment">
              <Avatar name={c.author_detail?.username} />
              <div className="comment__body">
                <span className="comment__author">{c.author_detail?.username || "User"}</span>
                <p className="comment__text">{c.text}</p>
                <span className="comment__time">{formatRelative(c.date_posted)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
      <form className="comment-form" onSubmit={submit}>
        <input
          type="text"
          className="form-input comment-form__input"
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

  const handleDelete = async () => {
    if (!window.confirm("Delete this post?")) return;
    await deletePost(post.id);
    onDelete(post.id);
  };

  return (
    <article className="post-card" aria-label={`Post by ${post.author_detail?.username}`}>
      {/* Header */}
      <div className="post-card__header">
        <Avatar name={post.author_detail?.username || post.author_detail?.email} />
        <div className="post-card__author-info">
          <span className="post-card__author-name">
            {post.author_detail?.username || "Learner"}
          </span>
          <span className="post-card__time">{formatRelative(post.date_posted)}</span>
        </div>
        <span className={`visibility-badge visibility-badge--${post.visibility?.toLowerCase()}`}>
          {visibilityIcon(post.visibility)} {post.visibility}
        </span>
        {isAuthor && (
          <button className="post-card__delete" onClick={handleDelete} aria-label="Delete post" title="Delete post">
            🗑
          </button>
        )}
      </div>

      {/* Content */}
      <p className="post-card__content">{post.content}</p>

      {/* Media */}
      {post.photo && (
        <img className="post-card__photo" src={post.photo} alt="Post photo" loading="lazy" />
      )}

      {/* Actions */}
      <div className="post-card__actions">
        <button
          className="post-action"
          onClick={handleReact}
          disabled={reacting}
          aria-label={`Like post. ${reactionCount} likes`}
        >
          ❤️ <span>{reactionCount}</span>
        </button>
        <button
          className="post-action"
          onClick={() => setShowComments(p => !p)}
          aria-expanded={showComments}
          aria-label={`Comments. ${post.comment_count} comments`}
        >
          💬 <span>{post.comment_count ?? 0}</span>
        </button>
        <button
          className="post-action"
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
  const [posts, setPosts]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage]       = useState(1);
  const [hasNext, setHasNext] = useState(false);

  const fetchPosts = async (p = 1) => {
    setLoading(true);
    try {
      const data = await getFeedPosts({ page: p });
      const results = data.results ?? data;
      setPosts(prev => p === 1 ? results : [...prev, ...results]);
      setHasNext(!!data.next);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { setTimeout(() => fetchPosts(1), 0); }, []);

  const handleCreated = (post) => setPosts(prev => [post, ...prev]);
  const handleDelete  = (id) => setPosts(prev => prev.filter(p => p.id !== id));
  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    fetchPosts(next);
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1 className="page-header__title">💬 Knowledge Feed</h1>
        <p className="page-header__subtitle">Share insights, ask peers, build knowledge together.</p>
      </div>

      <div className="feed-layout">
        {/* Create post */}
        <CreatePostForm onCreated={handleCreated} />

        {/* Posts */}
        {loading && posts.length === 0 ? (
          <div className="feed-loading">
            {[1,2,3].map(i => <div key={i} className="skeleton skeleton--post" />)}
          </div>
        ) : posts.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state__icon">💬</span>
            <p className="empty-state__msg">No posts yet. Be the first to share!</p>
          </div>
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
                disabled={loading}
              >
                {loading ? "Loading…" : "Load more"}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
