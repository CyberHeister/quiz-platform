/**
 * Quiz Platform Frontend - Main Entry Point
 */

import './styles/main.css';
import { QuizConfig } from './components/QuizConfig.js';
import { QuizRenderer } from './components/QuizRenderer.js';
import { getThemePreference, saveThemePreference } from './utils/storage.js';

// Application state
const state = {
  questions: [],
  answers: {},
  revealed: {},
  submitted: false,
  correctCount: 0,
  clickedOption: {},
  generator: {
    loading: false,
    error: null,
    lastRequest: null
  }
};

// Initialize components
const quizConfig = new QuizConfig(state, handleQuizUpdate);
const quizRenderer = new QuizRenderer(state, handleQuizUpdate);

function handleQuizUpdate() {
  if (state.questions.length > 0) {
    document.getElementById('configPanel').classList.add('hidden');
    document.getElementById('quizArea').classList.remove('hidden');
    document.getElementById('resetBtn').classList.remove('hidden');
    document.getElementById('summaryCard').classList.add('hidden');
    quizRenderer.renderQuiz();
  }
}

// Theme toggle
function initTheme() {
  const isDark = getThemePreference();
  document.documentElement.classList.toggle('dark', isDark);

  document.getElementById('themeBtn').addEventListener('click', () => {
    const current = document.documentElement.classList.contains('dark');
    const newDark = !current;
    document.documentElement.classList.toggle('dark', newDark);
    saveThemePreference(newDark);
  });
}

// Initialize application
function init() {
  initTheme();
  quizConfig.init();
  quizRenderer.init();

  console.log('Quiz Platform initialized');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
