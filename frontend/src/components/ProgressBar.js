/**
 * Progress bar component.
 * Displays answered count and progress percentage.
 */

export class ProgressBar {
  constructor(state) {
    this.state = state;
  }

  update() {
    const total = this.state.questions.length;
    const answered = this.getAnsweredCount();

    const textEl = document.getElementById('progressText');
    const fillEl = document.getElementById('progressFill');

    if (textEl) {
      textEl.textContent = total ? `Answered ${answered} of ${total}` : 'No questions loaded';
    }

    if (fillEl) {
      fillEl.style.width = total ? `${(answered / total) * 100}%` : '0%';
    }
  }

  getAnsweredCount() {
    return this.state.questions.reduce((count, _, idx) => {
      const answer = this.state.answers[idx];
      return count + (answer && answer.letters && answer.letters.length > 0 ? 1 : 0);
    }, 0);
  }
}
