/**
 * Quiz rendering component.
 * Renders question cards, options, and handles user interactions.
 */

import { grade } from '../utils/grading.js';

export class QuizRenderer {
  constructor(state, onUpdate) {
    this.state = state;
    this.onUpdate = onUpdate;
  }

  init() {
    this.bindGlobalEvents();
  }

  bindGlobalEvents() {
    // Submit all button
    document.getElementById('submitAllBtn').addEventListener('click', () => this.submitAll());

    // Reset buttons
    document.getElementById('resetBtn').addEventListener('click', () => this.reset());
    document.getElementById('resetAfterBtn').addEventListener('click', () => this.reset());

    // Review wrong button
    document.getElementById('reviewWrongBtn').addEventListener('click', () => this.scrollToFirstIncorrect());
  }

  renderQuiz() {
    const list = document.getElementById('questionsList');
    const paletteGrid = document.getElementById('paletteGrid');

    list.innerHTML = '';
    paletteGrid.innerHTML = '';

    this.state.questions.forEach((q, idx) => {
      // Create question card
      const card = document.createElement('div');
      card.className = 'card bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5';
      card.id = `q-${idx}`;
      card.innerHTML = this.buildQuestionHTML(q, idx);
      list.appendChild(card);

      // Create palette button
      const p = document.createElement('button');
      p.className = 'palette-btn w-8 h-8 text-xs rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition';
      p.textContent = q.id;
      p.addEventListener('click', () => card.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      paletteGrid.appendChild(p);
    });

    this.bindQuestionEvents();
    this.updateProgress();
  }

  buildQuestionHTML(q, idx) {
    const sel = (this.state.answers[idx] || { letters: [] }).letters;
    const isMulti = q.type === 'multi' || (q.correct && q.correct.length > 1);
    const displayOnly = !q.options.length;
    const type = isMulti ? 'checkbox' : 'radio';
    const hasSel = sel.length > 0;
    const revealed = !!this.state.revealed[idx];
    const g = this.state.submitted ? grade(q, sel) : { graded: false };
    const answerBody = [q.displayText, q.answerText].filter(Boolean).join('\n\n');
    const hasAnswer = q.correct.length > 0 || !!answerBody;

    // AI explanation buttons
    const aiBtns = `
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <span class="text-xs text-slate-500 dark:text-slate-400 font-medium mr-1">Explain:</span>
        <button data-ai="chatgpt" data-idx="${idx}" class="aiBtn px-3 py-1.5 rounded-lg bg-slate-900 dark:bg-slate-700 hover:opacity-90 text-white text-xs font-medium transition">🤖 Explain with ChatGPT</button>
        <button data-ai="gemini" data-idx="${idx}" class="aiBtn px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 hover:opacity-90 text-white text-xs font-medium transition">✦ Explain with Gemini</button>
      </div>`;

    // Answer box
    const answerBox = `
      <div class="answer-box rounded-xl border border-emerald-200 dark:border-emerald-800/70 bg-emerald-50/50 dark:bg-emerald-950/30 p-4 text-sm">
        <p class="font-semibold mb-1.5">Answer</p>
        ${q.correct.length ? `<p class="mb-1.5">Correct answer: <span class="font-semibold text-emerald-600 dark:text-emerald-400">${this.esc(q.correct.join(', '))}</span></p>` : ''}
        ${answerBody ? `<p class="text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line">${this.esc(answerBody)}</p>` : ''}
        ${aiBtns}
      </div>`;

    // Status badge
    let statusBadge = '';
    if (this.state.submitted) {
      if (!g.graded) statusBadge = '<span class="badge bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">Text answer</span>';
      else if (g.isCorrect) statusBadge = '<span class="badge-correct">✓ Correct</span>';
      else statusBadge = '<span class="badge-incorrect">✗ Incorrect</span>';
    } else if (hasSel) {
      statusBadge = '<span class="badge bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300">Answered</span>';
    }

    // Type badge
    const typeBadge = displayOnly
      ? '<span class="badge bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">Answer only</span>'
      : (isMulti
        ? '<span class="badge-multi">Multiple answers</span>'
        : '<span class="badge-single">Single answer</span>');

    // Header
    const head = `
      <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 class="font-semibold text-base">Question ${q.id}</h3>
        <div class="flex items-center gap-2">${typeBadge}${statusBadge}</div>
      </div>
      <p class="text-sm sm:text-[15px] leading-relaxed mb-4">${this.esc(q.text)}</p>`;

    // Display-only questions
    if (displayOnly) {
      if (hasAnswer) return head + answerBox;
      return head + '<p class="mt-3 text-xs text-amber-600 dark:text-amber-400">No answer key detected for this question.</p>';
    }

    // Options HTML
    const optsHTML = q.options.map((o, oi) => {
      const checked = sel.includes(o.letter);
      let cls = 'q-option flex items-start gap-3 border rounded-xl px-4 py-3 cursor-pointer ';
      let extra = '';

      if (this.state.submitted && g.graded) {
        const isCor = q.correct.includes(o.letter);
        if (isCor && checked) cls += 'correct';
        else if (isCor && !checked) {
          if (isMulti) { cls += 'missed'; extra = '<span class="ml-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400">Missing</span>'; }
          else cls += 'border-emerald-400 bg-emerald-50/60 dark:bg-emerald-900/20';
        }
        else if (checked && !isCor) cls += 'incorrect';
        else cls += 'border-slate-200 dark:border-slate-700 opacity-70';
      } else {
        cls += checked ? 'selected' : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-700';
      }

      const input = this.state.submitted
        ? `<input type="${type}" disabled ${checked ? 'checked' : ''} class="mt-1 w-4 h-4 ${type === 'radio' ? 'rounded-full' : 'rounded'} shrink-0">`
        : `<input type="${type}" name="opt-${idx}" value="${o.letter}" ${checked ? 'checked' : ''} class="mt-1 w-4 h-4 ${type === 'radio' ? 'rounded-full' : 'rounded'} shrink-0" data-idx="${idx}" data-letter="${o.letter}">`;

      return `<label class="${cls}">${input}<span class="text-sm">${extra}<span class="font-semibold">${this.esc(o.letter)})</span> ${this.esc(o.text)}</span></label>`;
    }).join('');

    // Feedback
    const feedback = this.state.submitted ? this.buildFeedbackHTML(q, idx, g, sel) : '';

    // Check button
    const checkBtn = this.state.submitted ? '' :
      `<button data-check="${idx}" class="checkBtn px-4 py-2 rounded-xl border text-sm font-medium transition ${revealed ? 'border-slate-400 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800' : 'border-indigo-500 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30'}">${revealed ? 'Hide Answer' : 'Check Answer'}</button>`;

    // Answer block
    const answerBlock = revealed ? (hasAnswer ? answerBox : '<p class="mt-3 text-xs text-amber-600 dark:text-amber-400">No answer key detected for this question.</p>') : '';

    return `
      ${head}
      <div class="space-y-2" data-qid="${idx}">${optsHTML}</div>
      ${answerBlock}
      <div class="mt-4 flex flex-wrap items-center gap-2">${checkBtn}</div>
      ${feedback}`;
  }

  buildFeedbackHTML(q, idx, g, sel) {
    const correctText = q.correct.length ? q.correct.join(', ') : (q.answerText ? 'No letter match — see answer text below' : 'No answer key');
    let box = '';
    if (!g.graded) {
      box = `
        <div class="mt-4 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-4 text-sm">
          <p class="font-semibold mb-1">Answer status</p>
          <p>Correct answer: <span class="font-semibold text-indigo-600 dark:text-indigo-400">${this.esc(correctText)}</span></p>
          ${q.answerText ? `<p class="mt-2 text-slate-600 dark:text-slate-300">${this.esc(q.answerText)}</p>` : ''}
          ${q.correct.length ? '<p class="mt-1 text-xs text-slate-500">This question is graded automatically.</p>' : ''}
        </div>`;
    } else if (g.isCorrect) {
      box = `
        <div class="mt-4 rounded-xl border border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 p-4 text-sm">
          <p class="font-semibold text-emerald-700 dark:text-emerald-400">✓ Correct</p>
          <p>Selected: <span class="font-semibold">${sel.join(', ') || 'none'}</span> · Correct: <span class="font-semibold">${q.correct.join(', ')}</span></p>
        </div>`;
    } else {
      const missing = g.missing.length ? `<span class="font-semibold text-amber-600 dark:text-amber-400">Missing: ${g.missing.join(', ')}</span>` : '';
      const extra = g.extra.length ? `<span class="font-semibold text-rose-600 dark:text-rose-400">Incorrect: ${g.extra.join(', ')}</span>` : '';
      box = `
        <div class="mt-4 rounded-xl border border-rose-500 bg-rose-50 dark:bg-rose-900/20 p-4 text-sm">
          <p class="font-semibold text-rose-700 dark:text-rose-400">✗ Incorrect</p>
          <p>Selected: <span class="font-semibold">${sel.join(', ') || 'none'}</span></p>
          <p>Correct answer: <span class="font-semibold text-emerald-600 dark:text-emerald-400">${q.correct.join(', ')}</span></p>
          <p class="mt-1">${missing} ${extra}</p>
        </div>`;
    }

    return `${box}
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <span class="text-xs text-slate-500 dark:text-slate-400 font-medium mr-1">Explain:</span>
        <button data-ai="chatgpt" data-idx="${idx}" class="aiBtn px-3 py-1.5 rounded-lg bg-slate-900 dark:bg-slate-700 hover:opacity-90 text-white text-xs font-medium transition">🤖 Explain with ChatGPT</button>
        <button data-ai="gemini" data-idx="${idx}" class="aiBtn px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 hover:opacity-90 text-white text-xs font-medium transition">✦ Explain with Gemini</button>
      </div>`;
  }

  bindQuestionEvents() {
    document.querySelectorAll('#questionsList .card').forEach((card, idx) => this.bindCardEvents(card, idx));
  }

  bindCardEvents(card, idx) {
    // Option selection
    card.querySelectorAll('input[data-idx]').forEach(inp => {
      inp.addEventListener('change', () => {
        const type = inp.type;
        const letters = (this.state.answers[idx] || { letters: [] }).letters;

        if (type === 'radio') {
          this.state.answers[idx] = { letters: [inp.value] };
          card.querySelectorAll('input[data-idx]').forEach(o => o.checked = o.value === inp.value);
        } else {
          const set = new Set(letters);
          inp.checked ? set.add(inp.value) : set.delete(inp.value);
          this.state.answers[idx] = { letters: [...set] };
        }

        this.updateProgress();
      });
    });

    // Check answer button
    card.querySelectorAll('.checkBtn').forEach(btn => {
      btn.addEventListener('click', () => {
        const i = parseInt(btn.dataset.check, 10);
        this.state.revealed[i] = !this.state.revealed[i];
        this.renderCard(i);
      });
    });

    // AI explanation buttons
    card.querySelectorAll('.aiBtn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openAI(btn.dataset.ai, parseInt(btn.dataset.idx, 10));
      });
    });
  }

  renderCard(idx) {
    const card = document.getElementById(`q-${idx}`);
    if (!card) return;
    card.innerHTML = this.buildQuestionHTML(this.state.questions[idx], idx);
    this.bindCardEvents(card, idx);
  }

  openAI(engine, idx) {
    const q = this.state.questions[idx];
    if (!q) return;

    const sel = (this.state.answers[idx] || { letters: [] }).letters;
    const opts = q.options.map(o => `${o.letter}) ${o.text}`).join('\n');
    const correct = q.correct.length ? q.correct.join(', ') : (q.answerText || 'Not provided');
    const selText = sel.length ? sel.join(', ') : 'Not answered';

    const prompt = [
      'Act as an expert exam coach and explain this multiple choice question in detail.',
      'QUESTION:',
      q.text,
      'OPTIONS:',
      opts || '(No options available)',
      'USER SELECTED ANSWER:',
      selText,
      'CORRECT ANSWER:',
      correct,
      'INSTRUCTION: Please explain in tabulated format why the correct answer(s) are right, why the selected option was correct or incorrect, and why the other options are wrong. Keep the explanation clear, precise and educational.'
    ].join('\n\n');

    const url = engine === 'chatgpt'
      ? `https://chatgpt.com/?q=${encodeURIComponent(prompt)}`
      : `https://gemini.google.com/app?q=${encodeURIComponent(prompt)}`;

    window.open(url, '_blank', 'noopener,noreferrer');
  }

  updateProgress() {
    const total = this.state.questions.length;
    const answered = this.state.questions.reduce((n, q, i) => n + (((this.state.answers[i] || { letters: [] }).letters.length) ? 1 : 0), 0);

    document.getElementById('progressText').textContent = total ? `Answered ${answered} of ${total}` : 'No questions loaded';
    document.getElementById('progressFill').style.width = total ? `${(answered / total) * 100}%` : '0%';

    if (this.state.submitted && total) {
      this.state.correctCount = this.state.questions.reduce((n, q, i) => {
        const g = grade(q, (this.state.answers[i] || { letters: [] }).letters);
        return n + (g.graded && g.isCorrect ? 1 : 0);
      }, 0);

      document.getElementById('scoreChip').textContent = `Score: ${this.state.correctCount} / ${total}`;
      const pct = Math.round(this.state.correctCount / total * 100);
      const chipClass = pct >= 70
        ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
        : pct >= 40
          ? 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300'
          : 'bg-rose-100 dark:bg-rose-900 text-rose-700 dark:text-rose-300';
      document.getElementById('scoreChip').className = `px-2 py-0.5 rounded-full text-xs font-semibold ${chipClass}`;
      this.renderSummary(pct);
    } else {
      document.getElementById('scoreChip').textContent = '';
    }

    // Update palette buttons
    document.querySelectorAll('#palette .palette-btn').forEach((b, i) => {
      const s = (this.state.answers[i] || { letters: [] }).letters;
      if (this.state.submitted) {
        const q = this.state.questions[i];
        const g = grade(q, s);
        b.className = `palette-btn w-8 h-8 text-xs rounded-lg border transition ${
          !g.graded ? 'border-slate-400 text-slate-500'
            : g.isCorrect ? 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300'
              : 'border-rose-500 bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300'
        }`;
      } else {
        const on = s.length > 0;
        b.className = `palette-btn w-8 h-8 text-xs rounded-lg border transition ${
          on ? 'active border-indigo-500 bg-indigo-500 text-white'
            : 'border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800'
        }`;
      }
    });
  }

  renderSummary(pct) {
    const total = this.state.questions.length;
    const graded = this.state.questions.reduce((n, q, i) => n + (grade(q, (this.state.answers[i] || { letters: [] }).letters).graded ? 1 : 0), 0);

    const body = document.getElementById('summaryBody');
    body.innerHTML = `
      <div class="flex items-center justify-center gap-8 my-4 flex-wrap">
        <div><p class="text-4xl font-black ${pct >= 70 ? 'text-emerald-500' : pct >= 40 ? 'text-amber-500' : 'text-rose-500'}">${pct}%</p><p class="text-xs text-slate-500 mt-1">Score</p></div>
        <div><p class="text-3xl font-bold">${this.state.correctCount}</p><p class="text-xs text-slate-500 mt-1">Correct</p></div>
        <div><p class="text-3xl font-bold text-slate-400">${total - this.state.correctCount}</p><p class="text-xs text-slate-500 mt-1">Incorrect</p></div>
        <div><p class="text-3xl font-bold text-indigo-500">${graded}</p><p class="text-xs text-slate-500 mt-1">Graded</p></div>
      </div>
      <p class="text-sm text-slate-600 dark:text-slate-400">${pct >= 70 ? 'Great job — keep practicing to lock it in!' : pct >= 40 ? 'Solid attempt — review the incorrect answers below.' : 'Keep going — review every explanation and try again.'}</p>`;

    document.getElementById('summaryCard').classList.remove('hidden');
    document.getElementById('summaryCard').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  submitAll() {
    if (!this.state.questions.length) return;
    this.state.submitted = true;
    this.renderQuiz();
  }

  reset() {
    this.state.answers = {};
    this.state.revealed = {};
    this.state.submitted = false;
    this.state.correctCount = 0;
    this.renderQuiz();
    document.getElementById('summaryCard').classList.add('hidden');
    document.getElementById('quizArea').classList.add('hidden');
    document.getElementById('configPanel').classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  scrollToFirstIncorrect() {
    const wrong = this.state.questions.findIndex((q, i) => {
      if (!this.state.submitted) return false;
      const g = grade(q, (this.state.answers[i] || { letters: [] }).letters);
      return g.graded && !g.isCorrect;
    });

    if (wrong >= 0) {
      document.getElementById(`q-${wrong}`).scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[c]));
  }
}
