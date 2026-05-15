import PropTypes from "prop-types";
import { formatRelative } from "../../lib/dateUtils";
import styles from "./FeedPostPreview.module.css";

/**
 * FeedPostPreview — Generic domain component for displaying a short snippet of a feed post.
 * Extracted to observe the DRY principle.
 */
export function FeedPostPreview({ post }) {
  return (
    <div className={styles.feedCard}>
      <div className={styles.feedAuthor}>
        <div className={styles.feedAvatar} aria-hidden="true">
          {post.author_detail?.username?.[0]?.toUpperCase() || "U"}
        </div>
        <div>
          <span className={styles.feedName}>
            {post.author_detail?.username || "User"}
          </span>
          <span className={styles.feedTime}>
            {formatRelative(post.date_posted)}
          </span>
        </div>
      </div>
      <p className={styles.feedContent}>
        {post.content?.slice(0, 120)}
        {post.content?.length > 120 ? "…" : ""}
      </p>
      <div className={styles.feedStats}>
        <div className={styles.feedStat}>
          <span>❤️</span>
          <span>{post.reaction_count ?? 0}</span>
        </div>
        <div className={styles.feedStat}>
          <span>💬</span>
          <span>{post.comment_count ?? 0}</span>
        </div>
      </div>
    </div>
  );
}

FeedPostPreview.propTypes = {
  post: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    content: PropTypes.string,
    date_posted: PropTypes.string,
    author_detail: PropTypes.shape({
      username: PropTypes.string,
    }),
    reaction_count: PropTypes.number,
    comment_count: PropTypes.number,
  }).isRequired,
};
