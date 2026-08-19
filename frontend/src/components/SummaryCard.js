/**
 * Summary card component.
 * Displays final score after quiz submission.
 */

import { calculateStats } from '../utils/grading.js';

export class SummaryCard {
  constructor(state) {
    this.state = state;
  }

  render() {
    const stats = calculateStats(this.state.questions, this.state.answers);
    const pct = stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0;

    const body = document.getElementById('summaryBody');
    if (!body) return;

    body.innerHTML = `
      <div class="flex items-center justify-center gap-8 my-4 flex-wrap">
        <div class="text-center">
          <p class="text-4xl font-black ${this.getScoreColor(pct)}">${pct}%</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Score</p>
        </div>
        <div class="text-center">
          <p class="text-3xl font-bold text-emerald-500">${stats.correct}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Correct</p>
        </div>
        <div class="text-center">
          <p class="text-3xl font-bold text-rose-500">${stats.incorrect}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Incorrect</p>
        </div>
        <div class="text-center">
          <p class="text-3xl font-bold text-indigo-500">${stats.graded}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Graded</p>
        </div>
      </div>
      <p class="text-sm text-slate-600 dark:text-slate-400 text-center">
        ${this.getMessage(pct)}
      </p>
    `;

    const card = document.getElementById('summaryCard');
    if (card) {
      card.classList.remove('hidden');
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  getScoreColor(pct) {
    if (pct >= 70) return 'text-emerald-500';
    if (pct >= 40) return 'text-amber-500';
    return 'text-rose-500';
  }

  getMessage(pct) {
    if (pct >= 70) return '🎉 Great job — keep practicing to lock it in!';
    if (pct >= 40) return '💪 Solid attempt — review the incorrect answers below.';
    return '📚 Keep going — review every explanation and try again.';
  }

  hide() {
    const card = document.getElementById('summaryCard');
    if (card) {
      card.classList.add('hidden');
    }
  }
}
