/**
 * Question parser utilities.
 * Parses MCQ questions from text files.
 */

/**
 * Parse questions from text content.
 * Supports standard MCQ format:
 * Q1. Question text
 * A) Option A
 * B) Option B
 * C) Option C
 * D) Option D
 * Answer: A
 */
export function parseQuestions(text) {
  const questions = [];
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

  let currentQ = null;
  let questionId = 1;

  for (const line of lines) {
    // Match question start: Q1., 1., Q1), etc.
    const qMatch = line.match(/^(?:Q)?(\d+)[.)]\s*(.+)/i);
    if (qMatch) {
      // Save previous question
      if (currentQ && currentQ.text && currentQ.options.length > 0) {
        questions.push(finalizeQuestion(currentQ));
      }
      currentQ = {
        id: qMatch[1],
        text: qMatch[2],
        options: [],
        correct: [],
        answerText: null,
        displayText: null
      };
      continue;
    }

    // Match option: A) text, A. text, a) text
    const optMatch = line.match(/^([A-Fa-f])[.)]\s*(.+)/);
    if (optMatch && currentQ) {
      currentQ.options.push({
        letter: optMatch[1].toUpperCase(),
        text: optMatch[2]
      });
      continue;
    }

    // Match answer: Answer: A, Ans: A,B, Correct: A
    const ansMatch = line.match(/^(?:Answer|Ans|Correct)[:\s]+([A-Fa-f, ]+)/i);
    if (ansMatch && currentQ) {
      currentQ.correct = ansMatch[1]
        .toUpperCase()
        .split(/[, ]+/)
        .filter(c => /^[A-F]$/.test(c));
      continue;
    }

    // Match explanation/answer text
    const expMatch = line.match(/^(?:Explanation|Exp|Reason)[:\s]+(.+)/i);
    if (expMatch && currentQ) {
      currentQ.answerText = expMatch[1];
      continue;
    }

    // Continuation of question text or option text
    if (currentQ) {
      if (currentQ.options.length === 0 && !line.match(/^[A-Fa-f][.)]/i)) {
        currentQ.text += ' ' + line;
      } else if (currentQ.options.length > 0 && !line.match(/^(?:Q)?\d+[.)]/i)) {
        // Append to last option
        const lastOpt = currentQ.options[currentQ.options.length - 1];
        if (lastOpt) {
          lastOpt.text += ' ' + line;
        }
      }
    }
  }

  // Don't forget the last question
  if (currentQ && currentQ.text && currentQ.options.length > 0) {
    questions.push(finalizeQuestion(currentQ));
  }

  return questions;
}

function finalizeQuestion(q) {
  const isMulti = q.correct.length > 1;

  return {
    id: q.id,
    type: isMulti ? 'multi' : 'single',
    text: q.text.trim(),
    options: q.options,
    correct: q.correct,
    explanation: q.answerText || null
  };
}

/**
 * Validate parsed questions.
 * Returns valid questions and any errors found.
 */
export function validateQuestions(questions) {
  const valid = [];
  const errors = [];

  questions.forEach((q, idx) => {
    // Check required fields
    if (!q.text || q.text.length < 5) {
      errors.push(`Question ${q.id}: Question text too short`);
      return;
    }

    if (!q.options || q.options.length < 2) {
      errors.push(`Question ${q.id}: Need at least 2 options`);
      return;
    }

    // Check all options have letters
    const letters = q.options.map(o => o.letter);
    if (new Set(letters).size !== letters.length) {
      errors.push(`Question ${q.id}: Duplicate option letters`);
      return;
    }

    // Validate correct answers
    if (q.correct.length === 0) {
      errors.push(`Question ${q.id}: No correct answer specified`);
      return;
    }

    const invalidCorrect = q.correct.filter(c => !letters.includes(c));
    if (invalidCorrect.length > 0) {
      errors.push(`Question ${q.id}: Invalid correct answer(s): ${invalidCorrect.join(', ')}`);
      return;
    }

    valid.push(q);
  });

  return { valid, errors };
}
