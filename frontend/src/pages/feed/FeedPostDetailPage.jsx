/**
 * FeedPostDetailPage.jsx
 */
import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import { getPost } from "../../services/feed.service";
import { askTutor } from "../../services/tutor.service";
import useAuthStore from "../../store/authStore";
import { PostCard } from "./FeedPage";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useQuery } from "@tanstack/react-query";
import styles from "./FeedPage.module.css";

export default function FeedPostDetailPage() {
  const { id } = useParams();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);

  const { data: post, isLoading: loading, isError } = useQuery({
    queryKey: ["post", id],
    queryFn: () => getPost(id),
  });

  const error = isError ? "Could not load post. It may have been deleted." : null;

  const [mwalimuResponse, setMwalimuResponse] = useState(null);
  const [askingMwalimu, setAskingMwalimu] = useState(false);

  const handleAskMwalimu = async () => {
    if (!post) return;
    setAskingMwalimu(true);
    setMwalimuResponse(null);
    try {
      const result = await askTutor(
        `Can you explain or provide more context on this post: "${post.content}"`,
        null,   // threadId — creates a new thread
        null,   // contextLessonId
        () => {} // onMessage — discard stream steps, only care about result
      );
      setMwalimuResponse(result.response || "Sorry, I could not generate an insight right now.");
    } catch {
      setMwalimuResponse("Sorry, I could not generate an insight right now.");
    } finally {
      setAskingMwalimu(false);
    }
  };

  useEffect(() => {

    if (post && location.state?.autoAskMwalimu && !mwalimuResponse && !askingMwalimu) {
      setTimeout(() => handleAskMwalimu(), 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post, location.state]);

  return (
    <div className="dashboard">
      <div className="page-header">
        <Link to="/learner/feed" className="btn btn-ghost btn-sm" style={{ alignSelf: "flex-start", padding: 0 }}>
          ← Back to Feed
        </Link>
        <h1 className="page-header__title">Post Detail</h1>
      </div>

      <div className={styles["feed-layout"]}>
        {loading ? (
          <div className="skeleton skeleton--card" />
        ) : error ? (
          <div className="alert-banner alert-banner--error">{error}</div>
        ) : post ? (
          <>
            <PostCard
              post={post}
              currentUserId={user?.user_id || user?.id}
              onDelete={() => { window.location.href = "/learner/feed"; }} 
            />

            {(askingMwalimu || mwalimuResponse) && (
              <div className="mwalimu-insight" style={{ marginTop: "1rem", padding: "1.5rem", background: "var(--color-primary-50)", borderRadius: "var(--radius-xl)", border: "1px solid var(--color-primary-200)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                  <div className="chat-bubble__avatar">🤖</div>
                  <strong style={{ color: "var(--color-primary-700)" }}>Mwalimu Insight</strong>
                </div>
                
                {askingMwalimu ? (
                  <div className="typing-indicator" aria-label="AI is thinking">
                    <span /><span /><span />
                  </div>
                ) : (
                  <div className="prose" style={{ background: "transparent", padding: 0, boxShadow: "none" }}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {mwalimuResponse}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
