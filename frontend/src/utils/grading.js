/**
 * Grading utilities for quiz questions.
 */

/**
 * Grade a single question against user selections.
 * @param {Object} q - Question object
 * @param {string[]} selLetters - Array of selected option letters
 * @returns {Object} Grading result
 */
export function grade(q, selLetters = []) {
  if (!q.correct || !q.correct.length || !q.options.length) {
    return { graded: false };
  }

  const corSet = new Set(q.correct);
  const selSet = new Set(selLetters);

  const missing = q.correct.filter(l => !selSet.has(l));
  const extra = selLetters.filter(l => !corSet.has(l));

  return {
    graded: true,
    isCorrect: missing.length === 0 && extra.length === 0,
    missing,
    extra
  };
}

/**
 * Calculate quiz statistics after submission.
 * @param {Array} questions - Array of question objects
 * @param {Object} answers - User answers object { idx: { letters: [] } }
 * @returns {Object} Quiz statistics
 */
export function calculateStats(questions, answers) {
  const total = questions.length;
  let correctCount = 0;
  let gradedCount = 0;

  questions.forEach((q, idx) => {
    const sel = (answers[idx] || { letters: [] }).letters;
    const result = grade(q, sel);

    if (result.graded) {
      gradedCount++;
      if (result.isCorrect) {
        correctCount++;
      }
    }
  });

  const percentage = total > 0 ? Math.round((correctCount / total) * 100) : 0;

  return {
    total,
    correctCount,
    incorrectCount: total - correctCount,
    gradedCount,
    percentage
  };
}
