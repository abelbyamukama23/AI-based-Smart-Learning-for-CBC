import { useState, useRef, useEffect } from "react";
import styles from "../TutorPage.module.css";

export function InteractiveSVG({ svgContent }) {
  const containerRef = useRef(null);
  const [tooltip, setTooltip] = useState({
    visible: false,
    text: "",
    x: 0,
    y: 0,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Inject cursor styles into elements that have data-annotation
    const elementsWithAnnotation = container.querySelectorAll("[data-annotation]");
    elementsWithAnnotation.forEach((el) => {
      el.style.cursor = "pointer";
      // Optional: Add a subtle transition if they have a fill or stroke
      el.style.transition = "all 0.2s ease";
    });

    const handleMouseOver = (e) => {
      let target = e.target;
      
      // Traverse up in case the user hovers over a nested element
      while (target && target !== container) {
        if (target.hasAttribute && target.hasAttribute("data-annotation")) {
          const text = target.getAttribute("data-annotation");
          setTooltip({
            visible: true,
            text,
            x: e.clientX,
            y: e.clientY,
          });
          
          // Visual highlight effect
          const originalOpacity = target.getAttribute("opacity") || "1";
          target.dataset.originalOpacity = originalOpacity;
          target.setAttribute("opacity", "0.7");
          return;
        }
        target = target.parentNode;
      }
    };

    const handleMouseMove = (e) => {
      setTooltip((prev) => {
        if (prev.visible) {
          return { ...prev, x: e.clientX, y: e.clientY };
        }
        return prev;
      });
    };

    const handleMouseOut = (e) => {
      let target = e.target;
      while (target && target !== container) {
        if (target.hasAttribute && target.hasAttribute("data-annotation")) {
          setTooltip((prev) => ({ ...prev, visible: false }));
          
          // Remove visual highlight
          if (target.dataset.originalOpacity !== undefined) {
            target.setAttribute("opacity", target.dataset.originalOpacity);
          }
          return;
        }
        target = target.parentNode;
      }
    };

    const handleContainerMouseLeave = () => {
      setTooltip((prev) => ({ ...prev, visible: false }));
    };

    container.addEventListener("mouseover", handleMouseOver);
    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseout", handleMouseOut);
    container.addEventListener("mouseleave", handleContainerMouseLeave);

    return () => {
      container.removeEventListener("mouseover", handleMouseOver);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseout", handleMouseOut);
      container.removeEventListener("mouseleave", handleContainerMouseLeave);
    };
  }, [svgContent]);

  return (
    <div className={styles["md-svg-interactive-wrapper"]}>
      <div
        ref={containerRef}
        className={styles["md-svg-container"]}
        dangerouslySetInnerHTML={{ __html: svgContent.replace(/\n$/, "") }}
      />
      {tooltip.visible && (
        <div
          className={styles["svg-tooltip"]}
          style={{
            position: "fixed",
            left: tooltip.x > window.innerWidth - 270 ? `${tooltip.x - 260}px` : `${tooltip.x + 15}px`,
            top: tooltip.y > window.innerHeight - 100 ? `${tooltip.y - 60}px` : `${tooltip.y + 15}px`,
          }}
        >
          {tooltip.text}
        </div>
      )}
    </div>
  );
}
