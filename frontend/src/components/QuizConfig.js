/**
 * Quiz configuration component.
 * Handles topic input, difficulty, count, type selection, and file upload.
 */

import { generateQuiz, convertApiQuestions } from '../api/quiz.js';
import { parseQuestions, validateQuestions } from '../utils/parser.js';

export class QuizConfig {
  constructor(state, onUpdate) {
    this.state = state;
    this.onUpdate = onUpdate;
    this.elements = {};
    this.debounceTimer = null;
    this.abortController = null;
  }

  init() {
    this.elements = {
      topicInput: document.getElementById('topicInput'),
      topicError: document.getElementById('topicError'),
      difficultySelect: document.getElementById('difficultySelect'),
      countInput: document.getElementById('countInput'),
      questionTypeRadios: document.querySelectorAll('input[name="questionType"]'),
      quizModeRadios: document.querySelectorAll('input[name="quizMode"]'),
      examTimerPresets: document.getElementById('examTimerPresets'),
      presetBtns: document.querySelectorAll('.preset-btn'),
      customTimerInput: document.getElementById('customTimerInput'),
      customTimerMinutes: document.getElementById('customTimerMinutes'),
      generateBtn: document.getElementById('generateBtn'),
      generateBtnText: document.getElementById('generateBtnText'),
      generateBtnSpinner: document.getElementById('generateBtnSpinner'),
      configStatus: document.getElementById('configStatus'),
      fileInput: document.getElementById('fileInput')
    };

    this.bindEvents();
    this.updateExamTimerVisibility();
  }

  bindEvents() {
    // Topic input validation with debounce
    this.elements.topicInput.addEventListener('input', (e) => {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => this.validateTopic(e.target.value), 300);
    });

    // Count input validation
    this.elements.countInput.addEventListener('change', (e) => {
      const val = parseInt(e.target.value);
      if (val < 1) e.target.value = 1;
      if (val > 50) e.target.value = 50;
    });

    // Quiz mode change - show/hide exam timer presets
    this.elements.quizModeRadios.forEach(radio => {
      radio.addEventListener('change', () => this.updateExamTimerVisibility());
    });

    // Exam timer preset buttons
    this.elements.presetBtns.forEach(btn => {
      btn.addEventListener('click', (e) => this.handlePresetClick(e.target));
    });

    // Generate button
    this.elements.generateBtn.addEventListener('click', () => this.handleGenerate());

    // File upload
    if (this.elements.fileInput) {
      this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }
  }

  updateExamTimerVisibility() {
    const selectedMode = document.querySelector('input[name="quizMode"]:checked')?.value || 'mock';
    if (selectedMode === 'exam') {
      this.elements.examTimerPresets.classList.remove('hidden');
    } else {
      this.elements.examTimerPresets.classList.add('hidden');
      this.elements.customTimerInput.classList.add('hidden');
    }
  }

  handlePresetClick(btn) {
    // Update active state
    this.elements.presetBtns.forEach(b => {
      b.classList.remove('border-indigo-500', 'bg-indigo-50', 'dark:bg-indigo-900/30');
      b.classList.add('border-slate-300', 'dark:border-slate-700');
    });
    btn.classList.remove('border-slate-300', 'dark:border-slate-700');
    btn.classList.add('border-indigo-500', 'bg-indigo-50', 'dark:bg-indigo-900/30');

    const preset = btn.dataset.preset;
    if (preset === 'custom') {
      this.elements.customTimerInput.classList.remove('hidden');
    } else {
      this.elements.customTimerInput.classList.add('hidden');
    }
  }

  getConfig() {
    const topic = this.elements.topicInput.value.trim();
    const difficulty = this.elements.difficultySelect.value;
    const count = parseInt(this.elements.countInput.value) || 10;
    const typeRadio = document.querySelector('input[name="questionType"]:checked');
    const questionType = typeRadio ? typeRadio.value : 'mixed';
    const modeRadio = document.querySelector('input[name="quizMode"]:checked');
    const quizMode = modeRadio ? modeRadio.value : 'mock';

    // Get exam timer duration if in exam mode
    let examTimerMinutes = null;
    if (quizMode === 'exam') {
      const activePreset = document.querySelector('.preset-btn.border-indigo-500')?.dataset.preset;
      if (activePreset === 'practitioner') examTimerMinutes = 90;
      else if (activePreset === 'associate') examTimerMinutes = 130;
      else if (activePreset === 'professional') examTimerMinutes = 170;
      else if (activePreset === 'custom') {
        examTimerMinutes = parseInt(this.elements.customTimerMinutes.value) || 60;
      }
    }

    return { topic, difficulty, count, questionType, quizMode, examTimerMinutes };
  }

  validateTopic(topic) {
    const error = this.elements.topicError;
    if (topic.length < 3) {
      error.textContent = 'Topic must be at least 3 characters';
      error.classList.remove('hidden');
      return false;
    }
    error.classList.add('hidden');
    return true;
  }

  getConfig() {
    const topic = this.elements.topicInput.value.trim();
    const difficulty = this.elements.difficultySelect.value;
    const count = parseInt(this.elements.countInput.value) || 10;
    const typeRadio = document.querySelector('input[name="questionType"]:checked');
    const questionType = typeRadio ? typeRadio.value : 'mixed';

    return { topic, difficulty, count, questionType };
  }

  async handleGenerate() {
    const config = this.getConfig();

    // Validate
    if (!this.validateTopic(config.topic)) return;

    // Abort any previous request
    if (this.abortController) {
      this.abortController.abort();
    }
    this.abortController = new AbortController();

    // Show loading state
    this.setLoading(true);

    try {
      const response = await generateQuiz(config);
      const questions = convertApiQuestions(response);

      if (questions.length === 0) {
        throw new Error('No questions were generated');
      }

      // Update state
      this.state.questions = questions;
      this.state.answers = {};
      this.state.revealed = {};
      this.state.submitted = false;
      this.state.correctCount = 0;
      this.state.clickedOption = {};
      this.state.generator = {
        loading: false,
        error: null,
        lastRequest: config
      };

      // Show metadata
      if (response.metadata) {
        this.elements.configStatus.textContent = `Generated via ${response.metadata.source} (${response.metadata.provider})`;
      }

      // Trigger UI update
      this.onUpdate();

    } catch (error) {
      if (error.name === 'AbortError') return;

      console.error('Quiz generation failed:', error);

      this.state.generator = {
        loading: false,
        error: error.message
      };

      this.showError(error.message);

    } finally {
      this.setLoading(false);
    }
  }

  setLoading(loading) {
    this.elements.generateBtn.disabled = loading;
    this.elements.generateBtnText.classList.toggle('hidden', loading);
    this.elements.generateBtnSpinner.classList.toggle('hidden', !loading);
  }

  showError(message) {
    // Create error toast
    const toast = document.createElement('div');
    toast.className = 'toast-error';
    toast.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="text-rose-500 text-xl">⚠️</span>
        <div>
          <p class="font-medium">Generation Failed</p>
          <p class="text-sm text-slate-600 dark:text-slate-400">${message}</p>
          <button class="mt-2 text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Retry</button>
        </div>
      </div>
    `;

    toast.querySelector('button').addEventListener('click', () => {
      toast.remove();
      this.handleGenerate();
    });

    document.getElementById('toastContainer').appendChild(toast);

    // Auto-remove after 8 seconds
    setTimeout(() => toast.remove(), 8000);
  }

  handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result;
        if (typeof text !== 'string') {
          throw new Error('Failed to read file');
        }

        const parsed = parseQuestions(text);
        const { valid, errors } = validateQuestions(parsed);

        if (errors.length > 0) {
          console.warn('Parse warnings:', errors);
        }

        if (valid.length === 0) {
          this.showError('No valid questions found in file');
          return;
        }

        // Update state with parsed questions
        this.state.questions = valid;
        this.state.answers = {};
        this.state.revealed = {};
        this.state.submitted = false;
        this.state.correctCount = 0;
        this.state.clickedOption = {};
        this.state.generator = {
          loading: false,
          error: null,
          lastRequest: { topic: `File: ${file.name}`, difficulty: 'custom', count: valid.length, questionType: 'mixed' }
        };

        this.elements.configStatus.textContent = `Loaded ${valid.length} questions from file`;
        this.onUpdate();

      } catch (err) {
        this.showError(err.message || 'Failed to parse file');
      }
    };

    reader.onerror = () => {
      this.showError('Failed to read file');
    };

    reader.readAsText(file);
  }

  reset() {
    this.elements.topicInput.value = '';
    this.elements.difficultySelect.value = 'medium';
    this.elements.countInput.value = 10;
    document.querySelector('input[name="questionType"][value="mixed"]').checked = true;
    this.elements.configStatus.textContent = '';
    this.elements.topicError.classList.add('hidden');
    if (this.elements.fileInput) {
      this.elements.fileInput.value = '';
    }
  }
}
