/**
 * LocalStorage helpers for quiz persistence.
 */

const STORAGE_KEY = 'quizlab';

/**
 * Get quiz theme preference.
 * @returns {boolean} True if dark mode enabled
 */
export function getThemePreference() {
  try {
    const saved = localStorage.getItem(`${STORAGE_KEY}-theme`);
    if (saved === 'dark') return true;
    if (saved === 'light') return false;
    // Follow system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
}

/**
 * Save quiz theme preference.
 * @param {boolean} isDark - Whether dark mode is enabled
 */
export function saveThemePreference(isDark) {
  try {
    localStorage.setItem(`${STORAGE_KEY}-theme`, isDark ? 'dark' : 'light');
  } catch {
    // Silently fail if storage unavailable
  }
}

/**
 * Get cached quiz questions (if valid).
 * @returns {Array|null} Cached questions or null
 */
export function getCachedQuiz() {
  try {
    const cached = localStorage.getItem(`${STORAGE_KEY}-quiz`);
    if (cached) {
      const data = JSON.parse(cached);
      // Cache expires after 1 hour
      if (Date.now() - data.timestamp < 3600000) {
        return data.questions;
      }
      // Clear expired cache
      localStorage.removeItem(`${STORAGE_KEY}-quiz`);
    }
  } catch {
    // Silently fail
  }
  return null;
}

/**
 * Save quiz questions to cache.
 * @param {Array} questions - Questions to cache
 */
export function saveQuizToCache(questions) {
  try {
    localStorage.setItem(`${STORAGE_KEY}-quiz`, JSON.stringify({
      questions,
      timestamp: Date.now()
    }));
  } catch {
    // Silently fail
  }
}
