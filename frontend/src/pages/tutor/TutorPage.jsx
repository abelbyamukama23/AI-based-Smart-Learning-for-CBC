import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { askTutor, getChatThread, getChatThreads } from "../../services/tutor.service";
import { extractApiError } from "../../lib/utils";

// ── Helpers ────────────────────────────────────────────────────────────────────
function formatTime(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Today";
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

// ── Chat Bubble ────────────────────────────────────────────────────────────────
function ChatBubble({ role, text, time, flagged }) {
  const isUser = role === "user";
  return (
    <div className={`chat-bubble chat-bubble--${isUser ? "user" : "ai"}`}>
      {!isUser && <div className="chat-bubble__avatar" aria-hidden>🤖</div>}
      <div className="chat-bubble__body">
        <div className="chat-bubble__text">
          {flagged && <span className="chat-bubble__flag" title="Out of scope">⚠️ </span>}
          {isUser ? (
            text
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
                h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
                h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
                strong: ({ children }) => <strong className="md-bold">{children}</strong>,
                ul: ({ children }) => <ul className="md-ul">{children}</ul>,
                ol: ({ children }) => <ol className="md-ol">{children}</ol>,
                li: ({ children }) => <li className="md-li">{children}</li>,
                hr: () => <hr className="md-hr" />,
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
                p: ({ children }) => <p className="md-p">{children}</p>,
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

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function TutorPage() {
  const location = useLocation();

  // ── Thread state ──
  const [threads, setThreads]       = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [threadsLoading, setThreadsLoading] = useState(true);

  // ── Message state ──
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "ai",
      text: "Habari! I'm **Mwalimu**. Ask me anything about your Uganda CBC curriculum — Mathematics, Science, English, SST, and more. Every question is a chance to learn something new! 🌱",
      time: formatTime(new Date().toISOString()),
      flagged: false,
    },
  ]);

  // ── Input / sending state ──
  const [query, setQuery]               = useState(location.state?.initialQuery || "");
  const [sending, setSending]           = useState(false);
  const [streamingStatus, setStreamingStatus] = useState("");
  const [error, setError]               = useState(null);
  const [sidebarOpen, setSidebarOpen]   = useState(true);

  // ── Voice input state ──
  const [listening, setListening]       = useState(false);
  const recognitionRef                  = useRef(null);

  // ── Image upload state ──
  const [imageFile, setImageFile]       = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const imageInputRef                   = useRef(null);

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // ── Load thread list ───────────────────────────────────────────────────────
  useEffect(() => {
    getChatThreads()
      .then(setThreads)
      .catch(() => {})
      .finally(() => setThreadsLoading(false));
  }, []);

  // ── Scroll to bottom on new message ───────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingStatus]);

  // ── Load a thread into the chat window ────────────────────────────────────
  const loadThread = useCallback(async (threadId) => {
    setActiveThreadId(threadId);
    setError(null);
    try {
      const thread = await getChatThread(threadId);
      const loaded = thread.interactions.flatMap((interaction) => [
        {
          id: `u-${interaction.id}`,
          role: "user",
          text: interaction.query,
          time: formatTime(interaction.timestamp),
        },
        {
          id: `a-${interaction.id}`,
          role: "ai",
          text: interaction.response || "",
          time: formatTime(interaction.timestamp),
          flagged: interaction.flagged_out_of_scope,
        },
      ]);
      setMessages(loaded.length > 0 ? loaded : [
        {
          id: "empty",
          role: "ai",
          text: "This thread is empty. Ask your first question!",
          time: "",
        },
      ]);
    } catch {
      setError("Failed to load this conversation.");
    }
  }, []);

  // ── Start a fresh conversation ─────────────────────────────────────────────
  const startNewChat = useCallback(() => {
    setActiveThreadId(null);
    setMessages([
      {
        id: "welcome",
        role: "ai",
        text: "Habari! I'm **Mwalimu**. Ask me anything about your Uganda CBC curriculum — Mathematics, Science, English, SST, and more. Every question is a chance to learn something new! 🌱",
        time: formatTime(new Date().toISOString()),
        flagged: false,
      },
    ]);
    setError(null);
    setQuery("");
    setImageFile(null);
    setImagePreview(null);
    inputRef.current?.focus();
  }, []);

  // ── Voice input ───────────────────────────────────────────────────────────
  const toggleVoice = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = "en-UG";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setQuery((prev) => (prev ? prev + " " + transcript : transcript));
    };
    rec.onerror = () => setListening(false);
    rec.onend   = () => setListening(false);
    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  }, [listening]);

  // ── Image picker ──────────────────────────────────────────────────────────
  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    inputRef.current?.focus();
  };

  const clearImage = () => {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImageFile(null);
    setImagePreview(null);
    if (imageInputRef.current) imageInputRef.current.value = "";
  };

  // ── Send a message ─────────────────────────────────────────────────────────
  const sendMessage = async (e) => {
    e.preventDefault();
    const text = query.trim();
    if ((!text && !imageFile) || sending) return;

    const sentImage = imageFile;
    setQuery("");
    setError(null);
    clearImage();

    const userMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      text: text || "📎 [Shared an image of their work]",
      imagePreview: sentImage ? URL.createObjectURL(sentImage) : null,
      time: formatTime(new Date().toISOString()),
    };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      setStreamingStatus("Thinking...");
      const result = await askTutor(
        text || "Please analyse the attached image of my work.",
        activeThreadId,
        null,
        (data) => {
          if (data.type === "status")       setStreamingStatus(data.message);
          if (data.type === "tool_call")    setStreamingStatus(`🔍 Looking up: ${data.name.replace(/_/g, " ")}...`);
          if (data.type === "thread_created") setActiveThreadId(data.thread_id);
        },
        sentImage
      );

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "ai",
          text: result.response || "I wasn't able to generate a response. Please try again.",
          time: formatTime(new Date().toISOString()),
          flagged: result.is_out_of_scope,
        },
      ]);

      if (result.threadId) {
        setActiveThreadId(result.threadId);
        getChatThreads().then(setThreads).catch(() => {});
      }
    } catch (err) {
      setError(extractApiError(err));
    } finally {
      setSending(false);
      setStreamingStatus("");
      inputRef.current?.focus();
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="tutor-page">
      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <aside className={`tutor-sidebar ${sidebarOpen ? "tutor-sidebar--open" : "tutor-sidebar--closed"}`}>
        <div className="tutor-sidebar__header">
          <button
            className="btn btn-primary btn-sm tutor-sidebar__new-btn"
            onClick={startNewChat}
            id="new-chat-btn"
          >
            ＋ New Chat
          </button>
          <button
            className="btn btn-ghost btn-icon tutor-sidebar__toggle"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? "◀" : "▶"}
          </button>
        </div>

        {sidebarOpen && (
          <div className="tutor-sidebar__list">
            {threadsLoading ? (
              <p className="tutor-sidebar__hint">Loading chats…</p>
            ) : threads.length === 0 ? (
              <p className="tutor-sidebar__hint">No conversations yet. Start one!</p>
            ) : (
              threads.map((t) => (
                <button
                  key={t.id}
                  className={`tutor-thread-item ${t.id === activeThreadId ? "tutor-thread-item--active" : ""}`}
                  onClick={() => loadThread(t.id)}
                  id={`thread-${t.id}`}
                >
                  <span className="tutor-thread-item__title">{t.title || "Untitled Chat"}</span>
                  <span className="tutor-thread-item__meta">
                    {formatDate(t.updated_at)} · {t.interaction_count} {t.interaction_count === 1 ? "turn" : "turns"}
                  </span>
                </button>
              ))
            )}
          </div>
        )}
      </aside>

      {/* ── Chat Area ──────────────────────────────────────────────────────── */}
      <div className="tutor-chat">
        {/* Header */}
        <div className="tutor-chat__header">
          <div className="tutor-chat__title">
            <span className="tutor-chat__avatar">🤖</span>
            <div>
              <h1 className="tutor-chat__name">Mwalimu</h1>
              <p className="tutor-chat__subtitle">Uganda CBC AI Tutor</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          className="chat-messages"
          aria-live="polite"
          aria-label="Chat conversation"
        >
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              role={msg.role}
              text={msg.text}
              time={msg.time}
              flagged={msg.flagged}
            />
          ))}

          {/* Live status indicator */}
          {sending && (
            <div className="chat-bubble chat-bubble--ai">
              <div className="chat-bubble__avatar" aria-hidden>🤖</div>
              <div className="chat-bubble__body">
                <div className="typing-indicator" aria-label="Mwalimu is thinking">
                  {streamingStatus && (
                    <span className="streaming-status-text">{streamingStatus}</span>
                  )}
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Error */}
        {error && <div className="chat-error" role="alert">{error}</div>}

        {/* Image preview strip */}
        {imagePreview && (
          <div className="chat-image-preview">
            <img src={imagePreview} alt="Your attached work" className="chat-image-preview__img" />
            <button type="button" className="chat-image-preview__remove" onClick={clearImage} aria-label="Remove image">✕</button>
          </div>
        )}

        {/* Input bar */}
        <form className="chat-input-bar" onSubmit={sendMessage} aria-label="Send a message to Mwalimu">
          {/* Hidden file input */}
          <input
            ref={imageInputRef}
            type="file"
            id="tutor-image-input"
            accept="image/*"
            style={{ display: "none" }}
            onChange={handleImageChange}
          />

          {/* Image upload button */}
          <button
            type="button"
            id="tutor-image-btn"
            className={`chat-input-bar__icon-btn${imageFile ? " chat-input-bar__icon-btn--active" : ""}`}
            onClick={() => imageInputRef.current?.click()}
            aria-label="Upload image of your work"
            title="Attach a photo of your handwritten work"
            disabled={sending}
          >📷</button>

          {/* Mic button */}
          <button
            type="button"
            id="tutor-mic-btn"
            className={`chat-input-bar__icon-btn${listening ? " chat-input-bar__icon-btn--listening" : ""}`}
            onClick={toggleVoice}
            aria-label={listening ? "Stop recording" : "Start voice input"}
            title={listening ? "Listening… click to stop" : "Ask by voice"}
            disabled={sending}
          >🎤</button>

          <textarea
            ref={inputRef}
            id="tutor-query"
            className="chat-input-bar__input"
            placeholder={listening ? "Listening… speak your question" : "Ask Mwalimu, or attach a photo of your work…"}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(e); }
            }}
            rows={2}
            aria-label="Your question"
            disabled={sending}
          />
          <button
            type="submit"
            id="tutor-send-btn"
            className="chat-input-bar__send btn btn-primary btn-sm"
            disabled={sending || (!query.trim() && !imageFile)}
            aria-label="Send message"
          >{sending ? "…" : "Send ➤"}</button>
        </form>
      </div>
    </div>
  );
}
