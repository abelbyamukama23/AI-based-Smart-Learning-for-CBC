/**
 * Formats a date string into a relative time description (e.g., "5m ago", "just now").
 * Extracted to observe the DRY principle.
 *
 * @param {string|Date} dateStr - The date to format
 * @returns {string} Relative time string
 */
export function formatRelative(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  
  return `${Math.floor(hrs / 24)}d ago`;
}
