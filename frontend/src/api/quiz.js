/**
 * API client for Quiz Platform backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Generate quiz questions via backend API.
 * @param {Object} params - Quiz generation parameters
 * @param {string} params.topic - Topic for question generation
 * @param {string} params.difficulty - Difficulty level: easy, medium, hard
 * @param {number} params.count - Number of questions (1-50)
 * @param {string} params.questionType - Type: single, multi, mixed
 * @returns {Promise<Object>} Quiz generation response
 */
export async function generateQuiz({ topic, difficulty, count, questionType }) {
  const response = await fetch(`${API_BASE_URL}/api/quiz/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      difficulty,
      count,
      question_type: questionType
    })
  });

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.detail?.message || data.error?.message || 'Failed to generate quiz');
    error.code = data.detail?.code || data.error?.code || 'UNKNOWN_ERROR';
    error.status = response.status;
    throw error;
  }

  if (!data.success || !data.questions) {
    throw new Error(data.detail?.message || data.error?.message || 'No questions generated');
  }

  return data;
}

/**
 * Check API health status.
 * @returns {Promise<Object>} Health check response
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/quiz/health`);
  return response.json();
}

/**
 * Convert API response to internal question format.
 * @param {Object} apiResponse - Response from /api/quiz/generate
 * @returns {Array} Array of internal question objects
 */
export function convertApiQuestions(apiResponse) {
  if (!apiResponse?.questions) return [];

  return apiResponse.questions.map((q, index) => ({
    id: q.id || index + 1,
    text: q.question,
    options: Object.entries(q.options).map(([letter, text]) => ({
      letter,
      text
    })),
    correct: q.correct_answers,
    answerText: q.explanation || '',
    displayText: '',
    type: q.type || 'single'
  }));
}
