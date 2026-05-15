import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { IconBot, IconUser } from "../../../components/Icons";
import { InteractiveSVG } from "./InteractiveSVG";
import styles from "../TutorPage.module.css";

export function ChatBubble({ role, text, flagged, onRetry, showRetry }) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className={`${styles["chat-bubble"]} ${styles[`chat-bubble--${isUser ? "user" : "ai"}`]}`}>

      <div className={styles["chat-bubble__body"]}>
        <div className={styles["chat-bubble__text"]}>
          {flagged && <span className={styles["chat-bubble__flag"]} title="Out of scope">⚠️ </span>}
          {isUser ? (
            text
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
              components={{
                h1: ({ children }) => <h1 className={styles["md-h1"]}>{children}</h1>,
                h2: ({ children }) => <h2 className={styles["md-h2"]}>{children}</h2>,
                h3: ({ children }) => <h3 className={styles["md-h3"]}>{children}</h3>,
                strong: ({ children }) => <strong className={styles["md-bold"]}>{children}</strong>,
                ul: ({ children }) => <ul className={styles["md-ul"]}>{children}</ul>,
                ol: ({ children }) => <ol className={styles["md-ol"]}>{children}</ol>,
                li: ({ children }) => <li className={styles["md-li"]}>{children}</li>,
                hr: () => <hr className={styles["md-hr"]} />,
                table: ({ children }) => (
                  <div className={styles["md-table-wrapper"]}>
                    <table className={styles["md-table"]}>{children}</table>
                  </div>
                ),
                th: ({ children }) => <th className={styles["md-th"]}>{children}</th>,
                td: ({ children }) => <td className={styles["md-td"]}>{children}</td>,
                code: ({ inline, className, children, ...props }) => {
                  const match = /language-(\w+)/.exec(className || "");
                  
                  // Handle inline SVG code blocks by rendering the InteractiveSVG directly
                  if (!inline && match && match[1] === "svg") {
                    return <InteractiveSVG svgContent={String(children)} />;
                  }
                  
                  if (inline) {
                    return <code className={styles["md-code-inline"]} {...props}>{children}</code>;
                  }
                  return (
                    <div className={styles["md-code-block-wrapper"]}>
                      <code className={`${styles["md-code-block"]} ${className || ""}`} {...props}>
                        {children}
                      </code>
                    </div>
                  );
                },
              }}
            >
              {text}
            </ReactMarkdown>
          )}
        </div>
        <div className={styles["chat-bubble__footer"]}>
          <div className={styles["chat-bubble__action-btns"]}>
            {/* Copy button — every message */}
            <button
              className={`${styles["chat-action-btn"]} ${copied ? styles["chat-action-btn--success"] : ""}`}
              onClick={handleCopy}
              title={copied ? "Copied!" : "Copy"}
              aria-label={copied ? "Copied" : "Copy"}
            >
              {copied ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              )}
            </button>
            {/* Retry button — user messages that were aborted/failed */}
            {isUser && showRetry && onRetry && (
              <button
                className={`${styles["chat-action-btn"]} ${styles["chat-action-btn--retry"]}`}
                onClick={() => onRetry(text)}
                title="Retry"
                aria-label="Retry message"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/></svg>
              </button>
            )}
          </div>
        </div>
      </div>
      {isUser && <div className={styles["chat-bubble__avatar"]} aria-hidden><IconUser size={20} /></div>}
    </div>
  );
}
