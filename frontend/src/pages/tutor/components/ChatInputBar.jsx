import { useEffect } from "react";
import styles from "../TutorPage.module.css";

export function ChatInputBar({
  imageFile,
  imageInputRef,
  handleImageChange,
  listening,
  toggleVoice,
  query,
  setQuery,
  sendMessage,
  sending,
  abortSending,
  inputRef,
}) {
  
  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [query, inputRef]);

  return (
    <div className={styles["chat-input-wrapper"]}>
      {/* Stop button — always rendered first so it stays visible when section is collapsed */}
      {sending && (
        <div className={styles["chat-stop-bar"]}>
          <button
            type="button"
            className={styles["chat-stop-btn"]}
            onClick={abortSending}
            aria-label="Stop generating"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
            </svg>
            Stop generating
          </button>
        </div>
      )}

      {/* Full input form — hidden below when Mwalimu is responding */}
      {!sending && (
        <form className={styles["chat-input-pill"]} onSubmit={sendMessage} aria-label="Send a message to Mwalimu">
          {/* Hidden file input */}
          <input
            ref={imageInputRef}
            type="file"
            id="tutor-image-input"
            accept="image/*"
            style={{ display: "none" }}
            onChange={handleImageChange}
          />

          {/* Left actions (Camera, Mic) */}
          <div className={styles["chat-input-actions"]}>
            <button
              type="button"
              className={`${styles["chat-input-btn"]} ${imageFile ? styles["chat-input-btn--active"] : ""}`}
              onClick={() => imageInputRef.current?.click()}
              aria-label="Upload image"
              title="Attach a photo"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
            </button>
            
            <button
              type="button"
              className={`${styles["chat-input-btn"]} ${listening ? styles["chat-input-btn--listening"] : ""}`}
              onClick={toggleVoice}
              aria-label={listening ? "Stop recording" : "Start voice input"}
              title="Voice input"
            >
              {listening ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="6" height="6"/></svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
              )}
            </button>
          </div>

          {/* Text Area */}
          <textarea
            ref={inputRef}
            id="tutor-query"
            className={styles["chat-input-textarea"]}
            placeholder={listening ? "Listening..." : "Message Mwalimu..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(e); }
            }}
            rows={1}
            aria-label="Your question"
          />

          {/* Send */}
          <div className={styles["chat-input-submit"]}>
            <button
              type="submit"
              className={`${styles["chat-submit-btn"]} ${query.trim() || imageFile ? styles["chat-submit-btn--active"] : ""}`}
              disabled={!query.trim() && !imageFile}
              aria-label="Send message"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </form>
      )}

      <div className={styles["chat-input-footer"]}>
        Mwalimu can make mistakes. Consider verifying important information.
      </div>
    </div>
  );
}
