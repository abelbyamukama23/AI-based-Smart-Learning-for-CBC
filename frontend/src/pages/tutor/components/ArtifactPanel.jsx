import React from "react";
import styles from "../TutorPage.module.css";
import { InteractiveSVG } from "./InteractiveSVG";

export function ArtifactPanel({ artifact, onClose }) {
  if (!artifact) return null;

  return (
    <div className={styles["artifact-panel"]}>
      <div className={styles["artifact-panel__header"]}>
        <div className={styles["artifact-panel__title"]}>
          <span>{artifact.type === "svg" ? "🎨" : "📄"}</span>
          <span>{artifact.title || "Interactive Illustration"}</span>
        </div>
        <button 
          className={styles["artifact-panel__close"]} 
          onClick={onClose}
          aria-label="Close artifact"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div className={styles["artifact-panel__content"]}>
        {artifact.type === "svg" ? (
          <InteractiveSVG svgContent={artifact.content} />
        ) : (
          <pre style={{ width: "100%", height: "100%", overflow: "auto" }}>
            <code>{artifact.content}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
