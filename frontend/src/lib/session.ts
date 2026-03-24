const SESSION_KEY = "featurevote_session_id";

/**
 * Returns a stable session ID for the current browser.
 * Generated once and persisted in localStorage.
 */
export function getSessionId(): string {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}
