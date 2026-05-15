import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { askTutor, getChatThread, getChatThreads } from "../../services/tutor.service";
import { extractApiError } from "../../lib/utils";
import { formatTime } from "./components/helpers";
import { ChatSidebar } from "./components/ChatSidebar";
import { ChatMessages } from "./components/ChatMessages";
import { ChatInputBar } from "./components/ChatInputBar";
import { ArtifactPanel } from "./components/ArtifactPanel";
import { useVoiceInput } from "../../hooks/useVoiceInput";
import { useImageAttachment } from "../../hooks/useImageAttachment";
import useAuthStore from "../../store/authStore";
import { MwalimuLogo } from "../../components/Icons";
import styles from "./TutorPage.module.css";

export default function TutorPage() {
  const location = useLocation();

  // ── Library context (passed from /library via router state) ──
  const libraryFile = location.state?.libraryFile ?? null;

  // ── User context ──
  const user = useAuthStore((s) => s.user);
  const firstName = user?.first_name ? ` ${user.first_name}` : "";

  // Build a context-aware welcome message when a library file is provided
  const welcomeText = libraryFile
    ? `Habari${firstName}! I'm **Mwalimu**. I can see you want to study **"${libraryFile.title}"**${
        libraryFile.subject_name ? ` (${libraryFile.subject_name})` : ""
      }. I've already loaded this material — ask me anything about it and I'll guide you through it step by step. 📖`
    : `Habari${firstName}! I'm **Mwalimu**. Ask me anything about your Uganda CBC curriculum — Mathematics, Science, English, SST, and more. Every question is a chance to learn something new! 🌱`;

  // ── Thread state ──
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");

  const { data: threads = [], isLoading: threadsLoading } = useQuery({
    queryKey: ["chatThreads", searchQuery],
    queryFn: () => getChatThreads(searchQuery),
  });

  const [activeThreadId, setActiveThreadId] = useState(null);

  // ── Message state ──
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "ai",
      text: welcomeText,
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
  const [libraryBannerVisible, setLibraryBannerVisible] = useState(!!libraryFile);
  const [mode, setMode]                 = useState("default");
  const [activeArtifact, setActiveArtifact] = useState(null);

  // ── Custom Hooks for Input ──
  const { listening, toggleVoice } = useVoiceInput({
    onResult: (transcript) => setQuery((prev) => (prev ? prev + " " + transcript : transcript)),
    onError: (msg) => setError(msg),
  });

  const { imageFile, imagePreview, imageInputRef, handleImageChange, clearImage } = useImageAttachment();

  // ── Abort / retry state ──
  const abortControllerRef              = useRef(null);   // holds current AbortController
  const [abortedMsgId, setAbortedMsgId] = useState(null); // id of last aborted user msg

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

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
    clearImage();
    inputRef.current?.focus();
  }, [clearImage]);

  // ── Abort sending ──────────────────────────────────────────────────────────
  const abortSending = () => {
    abortControllerRef.current?.abort();
  };

  // ── Retry last aborted query ───────────────────────────────────────────────
  const retryQuery = (text) => {
    setAbortedMsgId(null);
    setError(null);
    setQuery(text);
    // Small tick so state updates before synthetic submit
    setTimeout(() => {
      const fakeEvent = { preventDefault: () => {} };
      sendMessage(fakeEvent, text);
    }, 0);
  };

  // ── Send a message ─────────────────────────────────────────────────────────
  const sendMessage = async (e, overrideText) => {
    if (e?.preventDefault) e.preventDefault();
    const text = (overrideText ?? query).trim();
    if ((!text && !imageFile) || sending) return;

    // Create a fresh AbortController for this request
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const sentImage = imageFile;
    if (!overrideText) setQuery("");
    setError(null);
    setAbortedMsgId(null);
    clearImage();

    const userMsgId = `u-${Date.now()}`;
    const aiMsgId = `a-${Date.now()}`;
    
    const userMsg = {
      id: userMsgId,
      role: "user",
      text: text || "📎 [Shared an image of their work]",
      imagePreview: sentImage ? URL.createObjectURL(sentImage) : null,
      time: formatTime(new Date().toISOString()),
    };
    
    const initialAiMsg = {
      id: aiMsgId,
      role: "ai",
      text: "",
      time: formatTime(new Date().toISOString()),
    };
    
    setMessages((prev) => [...prev, userMsg, initialAiMsg]);
    setSending(true);

    try {
      setStreamingStatus("Thinking...");

      const isFirstMessage = messages.filter((m) => m.role === "user").length === 0;
      const queryWithContext =
        libraryFile && isFirstMessage
          ? `[Library context: The learner is studying "${libraryFile.title}"` +
            `${libraryFile.subject_name ? ` | Subject: ${libraryFile.subject_name}` : ""}` +
            `${libraryFile.class_level_name ? ` | Level: ${libraryFile.class_level_name}` : ""}` +
            `${libraryFile.description ? ` | Description: ${libraryFile.description}` : ""}` +
            `${libraryFile.tag_list?.length ? ` | Tags: ${libraryFile.tag_list.join(", ")}` : ""}` +
            `]\n\nLearner's question: ${text || "Please tell me about this material."}`
          : text || "Please analyse the attached image of my work.";

      const result = await askTutor(
        queryWithContext,
        activeThreadId,
        null,
        (data) => {
          if (data.type === "status")         setStreamingStatus(data.message);
          if (data.type === "tool_call")      setStreamingStatus(`🔍 Looking up: ${data.name.replace(/_/g, " ")}...`);
          if (data.type === "thread_created") setActiveThreadId(data.thread_id);
          if (data.type === "chunk") {
            setMessages((prev) => {
              const newMsgs = [...prev];
              const aiMsgIndex = newMsgs.findIndex(m => m.id === aiMsgId);
              if (aiMsgIndex !== -1) {
                newMsgs[aiMsgIndex] = { ...newMsgs[aiMsgIndex], text: newMsgs[aiMsgIndex].text + data.content };
              }
              return newMsgs;
            });
          }
        },
        sentImage,
        mode,
        controller.signal   // ← pass abort signal
      );

      // Overwrite the streamed text with the final sanitized response
      setMessages((prev) => {
        const newMsgs = [...prev];
        const aiMsgIndex = newMsgs.findIndex(m => m.id === aiMsgId);
        if (aiMsgIndex !== -1) {
          newMsgs[aiMsgIndex] = {
            ...newMsgs[aiMsgIndex],
            text: result.response || "I wasn't able to generate a response. Please try again.",
            flagged: result.is_out_of_scope,
          };
        }
        return newMsgs;
      });

      if (result.threadId) {
        setActiveThreadId(result.threadId);
        queryClient.invalidateQueries({ queryKey: ["chatThreads"] });
      }
    } catch (err) {
      if (err.name === "AbortError" || String(err.message).includes("abort")) {
        // User intentionally stopped — show retry on that message
        setAbortedMsgId(userMsgId);
        setError("Stopped. Use ↺ Retry to resend your question.");
      } else {
        setAbortedMsgId(userMsgId);
        setError(extractApiError(err) + " — Use ↺ Retry to try again.");
      }
    } finally {
      setSending(false);
      setStreamingStatus("");
      abortControllerRef.current = null;
      inputRef.current?.focus();
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className={`${styles["tutor-layout"]} ${activeArtifact ? styles["tutor-layout--artifact-open"] : ""} ${!sidebarOpen ? styles["tutor-layout--sidebar-closed"] : ""}`}>
      <ChatSidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        threadsLoading={threadsLoading}
        threads={threads}
        activeThreadId={activeThreadId}
        startNewChat={startNewChat}
        loadThread={loadThread}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      <div className={styles["tutor-chat"]}>
        {/* Header */}
        <div className={styles["tutor-chat__header"]}>
          <div className={styles["tutor-chat__title"]}>
            <span className={styles["tutor-chat__avatar"]}>
              <MwalimuLogo size={32} />
            </span>
            <div>
              <h1 className={styles["tutor-chat__name"]}>Mwalimu</h1>
              <p className={styles["tutor-chat__subtitle"]}>Uganda CBC AI Tutor</p>
            </div>
          </div>
          <div className={styles["tutor-chat__mode-selector"]}>
            <button 
              className={`${styles["mode-btn"]} ${mode === 'default' ? styles["mode-btn--active"] : ''}`}
              onClick={() => setMode('default')}
            >
              Default
            </button>
            <button 
              className={`${styles["mode-btn"]} ${mode === 'expert' ? styles["mode-btn--active"] : ''}`}
              onClick={() => setMode('expert')}
            >
              Expert
            </button>
            <button 
              className={`${styles["mode-btn"]} ${mode === 'professor' ? styles["mode-btn--active"] : ''}`}
              onClick={() => setMode('professor')}
            >
              Professor
            </button>
          </div>
        </div>

        {/* ── Library context banner ──────────────────────────────────────── */}
        {libraryFile && libraryBannerVisible && (
          <div className={styles["tutor-library-banner"]}>
            <span className={styles["tutor-library-banner__icon"]}>📚</span>
            <div className={styles["tutor-library-banner__text"]}>
              <strong>Reading:</strong> {libraryFile.title}
              {libraryFile.subject_name && (
                <span className={styles["tutor-library-banner__subject"]}> · {libraryFile.subject_name}</span>
              )}
              {libraryFile.class_level_name && (
                <span className={styles["tutor-library-banner__level"]}> · {libraryFile.class_level_name}</span>
              )}
            </div>
            {libraryFile.file_url && (
              <a
                href={libraryFile.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles["tutor-library-banner__link"]}
                title="Open file in new tab"
              >
                ⬇ Open
              </a>
            )}
            <button
              className={styles["tutor-library-banner__close"]}
              onClick={() => setLibraryBannerVisible(false)}
              aria-label="Dismiss library context banner"
            >
              ✕
            </button>
          </div>
        )}

        {messages.length === 0 ? (
          /* ── Empty state: welcome hero fills remaining space ── */
          <div className={styles["chat-welcome"]}>
            <div className={styles["chat-welcome__hero"]}>
              <MwalimuLogo size={80} className={styles["chat-welcome__logo"]} />
              <h2 className={styles["chat-welcome__title"]}>What would you like to learn today?</h2>
              <p className={styles["chat-welcome__subtitle"]}>
                Ask Mwalimu anything about the CBC curriculum — science, maths, languages, and more.
              </p>
            </div>
          </div>
        ) : (
          /* ── Active state: messages scroll ── */
          <>
            <ChatMessages
              messages={messages}
              sending={sending}
              streamingStatus={streamingStatus}
              abortedMsgId={abortedMsgId}
              retryQuery={retryQuery}
              bottomRef={bottomRef}
              onOpenArtifact={(type, content, title) => setActiveArtifact({ type, content, title })}
            />

            {error && (
              <div className={styles["chat-error"]} role="alert">
                {error}
                <button onClick={() => setError(null)} style={{marginLeft: "8px", background:"none", border:"none", cursor:"pointer"}}>✕</button>
              </div>
            )}
          </>
        )}

        {/* ── Input bar — always pinned to the bottom of the chat panel ── */}
        <div className={`${styles["chat-input-section"]} ${sending ? styles["chat-input-section--collapsed"] : ""}`}>
          {imagePreview && (
            <div className={styles["chat-image-preview"]}>
              <img src={imagePreview} alt="Your attached work" className={styles["chat-image-preview__img"]} />
              <button type="button" className={styles["chat-image-preview__remove"]} onClick={clearImage} aria-label="Remove image">✕</button>
            </div>
          )}
          <ChatInputBar
            imageFile={imageFile}
            imageInputRef={imageInputRef}
            handleImageChange={handleImageChange}
            listening={listening}
            toggleVoice={toggleVoice}
            query={query}
            setQuery={setQuery}
            sendMessage={sendMessage}
            sending={sending}
            abortSending={abortSending}
            inputRef={inputRef}
          />
        </div>

      </div>

      {activeArtifact && (
        <ArtifactPanel
          artifact={activeArtifact}
          onClose={() => setActiveArtifact(null)}
        />
      )}
    </div>
  );
}
