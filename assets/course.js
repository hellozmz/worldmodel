(() => {
  const quizzes = document.querySelectorAll('.quiz');
  quizzes.forEach((quiz, index) => {
    const options = quiz.querySelectorAll('.option');
    const feedback = quiz.querySelector('.feedback');
    const explanation = quiz.querySelector('.explanation');
    options.forEach(option => {
      option.addEventListener('click', () => {
        const isCorrect = option.dataset.correct === 'true';
        options.forEach(item => {
          item.disabled = true;
          if (item.dataset.correct === 'true') item.classList.add('correct');
        });
        if (!isCorrect) option.classList.add('incorrect');
        if (feedback) {
          feedback.textContent = isCorrect ? '✓ 正确' : '✕ 再想一下';
          feedback.className = `feedback ${isCorrect ? 'correct' : 'incorrect'}`;
        }
        if (explanation) explanation.classList.add('show');
        const event = new CustomEvent('quiz-answer', {
          bubbles: true,
          detail: { quiz: index + 1, correct: isCorrect }
        });
        quiz.dispatchEvent(event);
      });
    });
  });

  const progressChecks = document.querySelectorAll('.track input[type="checkbox"]');
  const bar = document.querySelector('.progress-bar span');
  const percentLabel = document.querySelector('.progress-percent');
  function updateProgress() {
    const checked = [...progressChecks].filter(item => item.checked).length;
    const percent = progressChecks.length ? Math.round(checked / progressChecks.length * 100) : 0;
    if (bar) bar.style.width = `${percent}%`;
    if (percentLabel) percentLabel.textContent = `${percent}%`;
    localStorage.setItem('worldmodel-course-progress', JSON.stringify(
      [...progressChecks].map(item => item.checked)
    ));
  }
  const saved = JSON.parse(localStorage.getItem('worldmodel-course-progress') || '[]');
  progressChecks.forEach((item, i) => item.checked = Boolean(saved[i]));
  progressChecks.forEach(item => item.addEventListener('change', updateProgress));
  updateProgress();

  document.querySelectorAll('.copy-command').forEach(button => {
    button.addEventListener('click', async () => {
      const target = document.querySelector(button.dataset.target);
      if (!target) return;
      await navigator.clipboard.writeText(target.innerText);
      const old = button.textContent;
      button.textContent = '已复制';
      setTimeout(() => button.textContent = old, 1200);
    });
  });
})();
