import { ChatBubble } from "./ChatBubble";
import { IconBot, MwalimuLogo } from "../../../components/Icons";
import styles from "../TutorPage.module.css";
export function ChatMessages({
  messages,
  sending,
  streamingStatus,
  abortedMsgId,
  retryQuery,
  bottomRef,
  onOpenArtifact,
}) {
  return (
    <div
      className={styles["chat-messages"]}
      aria-live="polite"
      aria-label="Chat conversation"
    >
      {messages.map((msg) => (
        <ChatBubble
          key={msg.id}
          role={msg.role}
          text={msg.text}
          flagged={msg.flagged}
          showRetry={msg.id === abortedMsgId}
          onRetry={retryQuery}
          onOpenArtifact={onOpenArtifact}
        />
      ))}

      {/* Live status indicator */}
      {sending && (
        <div className={`${styles["chat-bubble"]} ${styles["chat-bubble--ai"]}`}>
          <div className={styles["chat-bubble__avatar"]} aria-hidden>
            <MwalimuLogo size={36} />
          </div>
          <div className={styles["chat-bubble__body"]}>
            <div className="typing-indicator" aria-label="Mwalimu is thinking">
              {streamingStatus && (
                <span className={styles["streaming-status-text"]}>{streamingStatus}</span>
              )}
              <span /><span /><span />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
