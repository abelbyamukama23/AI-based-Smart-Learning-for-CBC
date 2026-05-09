import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { askTutor, getTutorHistory } from "../../services/tutor.service";
import { extractApiError } from "../../lib/utils";

function formatTime(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function ChatBubble({ role, text, time, flagged }) {
  const isUser = role === "user";
  return (
    <div className={`chat-bubble chat-bubble--${isUser ? "user" : "ai"}`}>
      {!isUser && (
        <div className="chat-bubble__avatar" aria-hidden>🤖</div>
      )}
      <div className="chat-bubble__body">
        <div className="chat-bubble__text">
          {flagged && (
            <span className="chat-bubble__flag" title="Out of scope">⚠️ </span>
          )}
          {isUser ? (
            text
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Headings
                h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
                h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
                h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
                // Bold
                strong: ({ children }) => <strong className="md-bold">{children}</strong>,
                // Lists
                ul: ({ children }) => <ul className="md-ul">{children}</ul>,
                ol: ({ children }) => <ol className="md-ol">{children}</ol>,
                li: ({ children }) => <li className="md-li">{children}</li>,
                // Horizontal rule
                hr: () => <hr className="md-hr" />,
                // Table
                table: ({ children }) => (
                  <div className="md-table-wrapper">
                    <table className="md-table">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="md-thead">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="md-tr">{children}</tr>,
                th: ({ children }) => <th className="md-th">{children}</th>,
                td: ({ children }) => <td className="md-td">{children}</td>,
                // Paragraphs
                p: ({ children }) => <p className="md-p">{children}</p>,
                // Code
                code: ({ children }) => <code className="md-code">{children}</code>,
              }}
            >
              {text}
            </ReactMarkdown>
          )}
        </div>
        <span className="chat-bubble__time">{time}</span>
      </div>
    </div>
  );
}


export default function TutorPage() {
  const location = useLocation();
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "ai",
      text: "Hello! I'm Mwalimu. Ask me anything related to your Uganda CBC curriculum — Mathematics, Science, SST, and more.",
      time: formatTime(new Date().toISOString()),
      flagged: false,
    },
  ]);
  const [query, setQuery]         = useState(location.state?.initialQuery || "");
  const [sending, setSending]     = useState(false);
  const [error, setError]         = useState(null);
  const [history, setHistory]     = useState([]);
  const [histLoading, setHistLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState("");

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // Load history on mount
  useEffect(() => {
    getTutorHistory()
      .then(data => setHistory(Array.isArray(data) ? data : (data.results ?? [])))
      .catch(() => {})
      .finally(() => setHistLoading(false));
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    const text = query.trim();
    if (!text || sending) return;

    setQuery("");
    setError(null);

    // Optimistically add user bubble
    const userMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      text,
      time: formatTime(new Date().toISOString()),
    };
    setMessages(prev => [...prev, userMsg]);
    setSending(true);

    try {
      setStreamingStatus("Thinking...");
      const session = await askTutor(text, null, (data) => {
        if (data.type === "status") {
          setStreamingStatus(data.message);
        } else if (data.type === "tool_call") {
          setStreamingStatus(`Using tool: ${data.name}...`);
        }
      });
      
      setMessages(prev => [
        ...prev,
        {
          id: session.id,
          role: "ai",
          text: session.response,
          time: formatTime(session.timestamp),
          flagged: session.flagged_out_of_scope,
        },
      ]);
      // Refresh history count
      setHistory(prev => [session, ...prev]);
    } catch (err) {
      setError(extractApiError(err));
      // Remove the user message if AI failed completely
    } finally {
      setSending(false);
      setStreamingStatus("");
      inputRef.current?.focus();
    }
  };

  const loadHistorySession = (session) => {
    setMessages(prev => [
      ...prev,
      { id: `uh-${session.id}`, role: "user", text: session.query, time: formatTime(session.timestamp) },
      { id: `ah-${session.id}`, role: "ai", text: session.response, time: formatTime(session.timestamp), flagged: session.flagged_out_of_scope },
    ]);
    setShowHistory(false);
  };

  return (
    <div className="dashboard tutor-page">
      <div className="page-header">
        <h1 className="page-header__title">🤖 Mwalimu</h1>
        <p className="page-header__subtitle">
          CBC-aligned answers in seconds. Powered by AI.
        </p>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => setShowHistory(h => !h)}
          aria-expanded={showHistory}
        >
          {showHistory ? "Hide" : "Show"} History ({history.length})
        </button>
      </div>

      <div className="tutor-layout">
        {/* ── Session history panel ─────────────────────────────────────── */}
        {showHistory && (
          <aside className="tutor-history">
            <h2 className="tutor-history__title">Past Sessions</h2>
            {histLoading ? (
              <p className="tutor-history__loading">Loading…</p>
            ) : history.length === 0 ? (
              <p className="tutor-history__empty">No past sessions yet.</p>
            ) : (
              <ul className="tutor-history__list">
                {history.map(s => (
                  <li key={s.id}>
                    <button
                      className="tutor-history__item"
                      onClick={() => loadHistorySession(s)}
                    >
                      <span className="tutor-history__query">{s.query?.slice(0, 60)}…</span>
                      <span className="tutor-history__time">{formatTime(s.timestamp)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        )}

        {/* ── Chat area ─────────────────────────────────────────────────── */}
        <div className="chat-container">
          <div className="chat-messages" aria-live="polite" aria-label="Chat conversation">
            {messages.map(msg => (
              <ChatBubble
                key={msg.id}
                role={msg.role}
                text={msg.text}
                time={msg.time}
                flagged={msg.flagged}
              />
            ))}

            {/* Typing indicator */}
            {sending && (
              <div className="chat-bubble chat-bubble--ai">
                <div className="chat-bubble__avatar" aria-hidden>🤖</div>
                <div className="chat-bubble__body">
                  <div className="typing-indicator" aria-label="AI is thinking">
                    {streamingStatus && (
                      <span className="streaming-status-text" style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginRight: "8px", fontStyle: "italic" }}>
                        {streamingStatus}
                      </span>
                    )}
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Error */}
          {error && (
            <div className="chat-error" role="alert">{error}</div>
          )}

          {/* Input */}
          <form className="chat-input-bar" onSubmit={sendMessage} aria-label="Send a message">
            <textarea
              ref={inputRef}
              id="tutor-query"
              className="chat-input-bar__input"
              placeholder="Ask a question about your CBC curriculum…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(e);
                }
              }}
              rows={2}
              aria-label="Your question"
              disabled={sending}
            />
            <button
              type="submit"
              className="chat-input-bar__send btn btn-primary btn-sm"
              disabled={sending || !query.trim()}
              aria-label="Send message"
            >
              {sending ? "…" : "Send"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
