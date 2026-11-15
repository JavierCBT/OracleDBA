/**
 * OracleDBA Exam Simulator Core Engine
 * Unified engine for 1Z0-078 and 1Z0-083 simulators.
 * Supports Desktop, Tablet (Touch/Swipe), and Offline PWA.
 */

(function (global) {
  'use strict';

  let config = {
    examId: '',
    examTitle: '',
    examBadge: '',
    dataPath: '',
    examCount: 60,
    timeLimitSeconds: 7200,
    storageKey: '',
    thresholdKey: '',
    legacyStorageKey: '',
    legacyThresholdKey: ''
  };

  let ALL_QUESTIONS = [];
  let currentIndex = 0;
  let currentQuestionId = null;
  let userStats = {};
  let masteryThreshold = 3;
  let currentMode = 'study'; // 'study', 'exam', 'weak', 'memory'
  let selectedAnswers = new Set();
  let checkedCurrent = false;

  let examQuestions = [];
  let examAnswers = {};
  let examTimerInterval = null;
  let examSecondsRemaining = 7200;

  // Touch swipe support for tablets/phones
  let touchStartX = 0;
  let touchStartY = 0;

  function initExamSimulator(userConfig) {
    config = Object.assign(config, userConfig);

    // Setup Storage Keys
    if (!config.storageKey) config.storageKey = `oracle_dba_stats_${config.examId}`;
    if (!config.thresholdKey) config.thresholdKey = `oracle_dba_threshold_${config.examId}`;

    // Migrate legacy progress if present
    migrateLegacyStorage();

    // Load saved settings
    const savedThreshold = localStorage.getItem(config.thresholdKey);
    if (savedThreshold) {
      masteryThreshold = parseInt(savedThreshold, 10);
      const sel = document.getElementById('threshold-select');
      if (sel) sel.value = masteryThreshold;
    }

    const savedStats = localStorage.getItem(config.storageKey);
    if (savedStats) {
      try {
        userStats = JSON.parse(savedStats);
      } catch (e) {
        userStats = {};
      }
    }

    // Attach event listeners
    initEventListeners();

    // Fetch question data
    fetch(config.dataPath)
      .then(response => {
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        return response.json();
      })
      .then(questions => {
        ALL_QUESTIONS = questions;
        buildResetModal();
        updateHeaderStats();
        renderCurrentQuestion();
      })
      .catch(err => {
        console.error('Failed to load exam data:', err);
        const container = document.getElementById('quiz-container');
        if (container) {
          container.innerHTML = `
            <div class="question-card" style="text-align:center; padding:30px; border-color:var(--error);">
              <h3 style="color:var(--error);">Failed to load questions dataset</h3>
              <p style="color:var(--text-muted); margin-top:8px;">${escapeHtml(err.message)}</p>
              <button class="primary" style="margin-top:16px;" onclick="location.reload()">Retry</button>
            </div>
          `;
        }
      });
  }

  function migrateLegacyStorage() {
    if (config.legacyStorageKey && !localStorage.getItem(config.storageKey)) {
      const legacyData = localStorage.getItem(config.legacyStorageKey);
      if (legacyData) {
        localStorage.setItem(config.storageKey, legacyData);
      }
    }
    if (config.legacyThresholdKey && !localStorage.getItem(config.thresholdKey)) {
      const legacyThreshold = localStorage.getItem(config.legacyThresholdKey);
      if (legacyThreshold) {
        localStorage.setItem(config.thresholdKey, legacyThreshold);
      }
    }
  }

  function initEventListeners() {
    // Keyboard navigation
    window.addEventListener('keydown', event => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (document.querySelector('.modal.active')) return;
      if (event.target.closest('input, textarea, select, [contenteditable="true"]')) return;

      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        prevQuestion();
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        nextQuestion();
      }
    });

    // Touch swipe gestures for tablets and mobiles
    window.addEventListener('touchstart', e => {
      if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    window.addEventListener('touchend', e => {
      if (document.querySelector('.modal.active')) return;
      if (e.target.closest('input, select, textarea, button, pre')) return;

      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const diffX = touchEndX - touchStartX;
      const diffY = touchEndY - touchStartY;

      // Ensure horizontal swipe: abs(X) > 60px and abs(Y) < 50px
      if (Math.abs(diffX) > 60 && Math.abs(diffY) < 50) {
        if (diffX < 0) {
          nextQuestion(); // swipe left -> next
        } else {
          prevQuestion(); // swipe right -> previous
        }
      }
    }, { passive: true });
  }

  function updateHeaderStats() {
    const totalEl = document.getElementById('stat-total');
    if (totalEl) totalEl.innerText = ALL_QUESTIONS.length;

    let masteredCount = 0;
    let totalAttempts = 0;
    let totalCorrect = 0;
    let weakCount = 0;

    ALL_QUESTIONS.forEach(q => {
      const s = userStats[q.id];
      if (s) {
        if (s.mastered) masteredCount++;
        if (s.streak === 0 && s.wrong > 0) weakCount++;
        totalAttempts += (s.correct + s.wrong);
        totalCorrect += s.correct;
      }
    });

    const masteredEl = document.getElementById('stat-mastered');
    if (masteredEl) masteredEl.innerText = masteredCount;

    const weakEl = document.getElementById('weak-count');
    if (weakEl) weakEl.innerText = weakCount;

    const accEl = document.getElementById('stat-acc');
    if (accEl) {
      const acc = totalAttempts > 0 ? Math.round((totalCorrect / totalAttempts) * 100) : 0;
      accEl.innerText = `${acc}%`;
    }

    const filtered = getFilteredQuestions();
    const activeEl = document.getElementById('stat-active');
    if (activeEl) activeEl.innerText = filtered.length;
  }

  function getFilteredQuestions() {
    if (currentMode === 'exam') return examQuestions;

    const searchInput = document.getElementById('search-input');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const hideMastered = document.getElementById('hide-mastered') ? document.getElementById('hide-mastered').checked : false;

    return ALL_QUESTIONS.filter(q => {
      const s = userStats[q.id];
      if (currentMode === 'weak') {
        const isWeak = s && s.streak === 0 && s.wrong > 0;
        if (!isWeak) return false;
      } else if (hideMastered && s && s.mastered) {
        return false;
      }

      if (query) {
        const numMatch = query.match(/^#?(\d+)$/);
        if (numMatch) {
          return q.id === parseInt(numMatch[1], 10);
        }
        const textMatch = (q.text || '').toLowerCase().includes(query);
        const domainMatch = (q.domain || '').toLowerCase().includes(query);
        const optMatch = (q.options || []).some(o => (o.text || '').toLowerCase().includes(query));
        const expMatch = (q.explanation || '').toLowerCase().includes(query);
        return textMatch || domainMatch || optMatch || expMatch;
      }
      return true;
    });
  }

  function setMode(mode) {
    currentMode = mode;
    currentIndex = 0;
    selectedAnswers.clear();
    checkedCurrent = false;

    ['study', 'exam', 'weak', 'memory'].forEach(m => {
      const tab = document.getElementById(`tab-${m}`);
      if (tab) tab.classList.remove('active');
    });
    const activeTab = document.getElementById(`tab-${mode}`);
    if (activeTab) activeTab.classList.add('active');

    const filtersEl = document.getElementById('study-filters');
    const examControls = document.getElementById('exam-controls');

    if (mode === 'exam') {
      if (filtersEl) filtersEl.style.display = 'none';
      if (examControls) examControls.style.display = 'flex';
      startExam();
    } else {
      if (filtersEl) filtersEl.style.display = 'flex';
      if (examControls) examControls.style.display = 'none';
      if (examTimerInterval) clearInterval(examTimerInterval);
      renderCurrentQuestion();
    }
  }

  // Fisher-Yates (Knuth) unbiased shuffle algorithm
  function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  function startExam() {
    const shuffled = shuffleArray(ALL_QUESTIONS);
    const count = Math.min(config.examCount, ALL_QUESTIONS.length);
    examQuestions = shuffled.slice(0, count);
    examAnswers = {};
    examSecondsRemaining = config.timeLimitSeconds || 7200;
    currentIndex = 0;

    if (examTimerInterval) clearInterval(examTimerInterval);
    updateTimerDisplay();

    examTimerInterval = setInterval(() => {
      examSecondsRemaining--;
      updateTimerDisplay();
      if (examSecondsRemaining <= 0) {
        clearInterval(examTimerInterval);
        alert('Time limit reached! Submitting exam automatically.');
        finishExam();
      }
    }, 1000);

    renderCurrentQuestion();
  }

  function updateTimerDisplay() {
    const timerEl = document.getElementById('exam-timer');
    if (!timerEl) return;
    const mins = Math.floor(examSecondsRemaining / 60);
    const secs = examSecondsRemaining % 60;
    timerEl.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }

  function renderCurrentQuestion() {
    const filtered = getFilteredQuestions();
    const container = document.getElementById('quiz-container');
    if (!container) return;

    if (filtered.length === 0) {
      currentQuestionId = null;
      container.innerHTML = questionNavigationMarkup('0 of 0') + `
        <div class="question-card" style="text-align:center; padding:40px;">
          <h3>🎉 No pending questions in this filter!</h3>
          <p style="color:var(--text-muted); margin-top:10px;">You have mastered all questions or no questions matched your search criteria.</p>
          <button style="margin-top:16px;" onclick="document.getElementById('hide-mastered').checked=false; renderCurrentQuestion();">Show Mastered Questions</button>
        </div>
      `;
      return;
    }

    if (currentIndex >= filtered.length) currentIndex = 0;
    if (currentIndex < 0) currentIndex = filtered.length - 1;

    const q = filtered[currentIndex];
    currentQuestionId = q.id;
    selectedAnswers.clear();
    checkedCurrent = false;

    if (currentMode === 'exam' && examAnswers[q.id]) {
      selectedAnswers = new Set(examAnswers[q.id]);
    }

    const s = userStats[q.id] || { streak: 0, correct: 0, wrong: 0, mastered: false };
    const counterText = `${currentIndex + 1} of ${filtered.length}`;

    let reqBadge = `<span class="badge badge-req single">Single Choice</span>`;
    if (q.type === 'multiple' || q.select_count > 1) {
      reqBadge = `<span class="badge badge-req">Choose ${q.select_count}</span>`;
    }

    const statusBadge = q.review_status === 'ambiguous'
      ? `<span class="badge badge-ambiguous" title="${escapeHtml(q.review_note || '')}">⚠️ Ambiguous</span>`
      : `<span class="badge badge-verified">✓ Verified</span>`;

    let optionsMarkup = '';
    const isMemory = (currentMode === 'memory');

    (q.options || []).forEach(opt => {
      const key = opt.letter || opt.key;
      const isCorrect = q.correct.includes(key);
      const isSelected = selectedAnswers.has(key);

      let classes = 'option-label';
      if (isMemory) {
        classes += isCorrect ? ' memory-correct' : ' memory-dimmed';
      } else if (isSelected) {
        classes += ' selected';
      }

      optionsMarkup += `
        <div class="${classes}" id="opt-${key}" onclick="OracleApp.toggleOption('${key}')">
          <div class="option-box"></div>
          <span class="option-prefix">${key}.</span>
          <span class="option-text">${escapeHtml(opt.text)}</span>
        </div>
      `;
    });

    let actionBtn = '';
    if (currentMode === 'exam') {
      actionBtn = `<button class="primary" onclick="OracleApp.nextQuestion()">Next Question &gt;</button>`;
    } else if (currentMode !== 'memory') {
      actionBtn = `<button class="primary" id="btn-verify" onclick="OracleApp.verifyAnswer()">Check Answer</button>`;
    }

    container.innerHTML = `
      ${questionNavigationMarkup(counterText, q.id)}
      <div class="question-card" id="card-${q.id}">
        <div class="q-meta">
          <div class="badges">
            <span class="badge badge-id">#${q.id}</span>
            <span class="badge badge-domain">${(q.domain || '').toUpperCase()}</span>
            ${reqBadge}
            ${statusBadge}
          </div>
          <div class="streak-indicator">
            Streak: <strong>${s.streak} / ${masteryThreshold}</strong>
            ${s.mastered ? '<span style="color:var(--success); margin-left:6px;">(Mastered)</span>' : ''}
            ${s.streak > 0 ? `<button style="padding:2px 8px; font-size:0.75rem; margin-left:8px;" onclick="OracleApp.resetQuestionStreak(${q.id})">Reset</button>` : ''}
          </div>
        </div>

        <div class="q-text">${renderQuestionBody(q.text)}</div>
        <div class="options-container">${optionsMarkup}</div>

        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          ${actionBtn}
        </div>

        <div id="explanation-area" style="display:${isMemory ? 'block' : 'none'};">
          ${isMemory ? reviewExplanationMarkup(q) : ''}
        </div>
      </div>
      ${questionNavigationMarkup(counterText, q.id)}
    `;

    updateHeaderStats();
  }

  function questionNavigationMarkup(counterText, curId = '') {
    return `
      <div class="bottom-nav">
        <button type="button" class="nav-prev" onclick="OracleApp.prevQuestion()" aria-label="Previous question">&lt; Previous</button>
        <div class="nav-middle">
          <form class="question-jump" onsubmit="OracleApp.jumpToQuestion(event)">
            <label for="question-jump-input">Go to #</label>
            <input type="number" id="question-jump-input" min="1" max="${ALL_QUESTIONS.length}" step="1" value="${curId}" inputmode="numeric" aria-label="Question number to display">
            <button type="submit">Go</button>
          </form>
          <span style="font-size:0.85rem; color:var(--text-muted);">${counterText}</span>
          <div class="q-jump-feedback" aria-live="polite"></div>
        </div>
        <button type="button" class="nav-next" onclick="OracleApp.nextQuestion()" aria-label="Next question">Next &gt;</button>
      </div>
    `;
  }

  function toggleOption(key) {
    if (checkedCurrent || currentMode === 'memory') return;

    const filtered = getFilteredQuestions();
    const q = filtered[currentIndex];
    const maxSelect = q.select_count || 1;

    if (maxSelect === 1) {
      selectedAnswers.clear();
      selectedAnswers.add(key);
      document.querySelectorAll('.option-label').forEach(el => el.classList.remove('selected'));
      const el = document.getElementById(`opt-${key}`);
      if (el) el.classList.add('selected');
    } else {
      const el = document.getElementById(`opt-${key}`);
      if (selectedAnswers.has(key)) {
        selectedAnswers.delete(key);
        if (el) el.classList.remove('selected');
      } else {
        if (selectedAnswers.size >= maxSelect) {
          const firstKey = selectedAnswers.values().next().value;
          selectedAnswers.delete(firstKey);
          const firstEl = document.getElementById(`opt-${firstKey}`);
          if (firstEl) firstEl.classList.remove('selected');
        }
        selectedAnswers.add(key);
        if (el) el.classList.add('selected');
      }
    }

    if (currentMode === 'exam') {
      examAnswers[q.id] = Array.from(selectedAnswers);
    }
  }

  function verifyAnswer() {
    if (checkedCurrent || currentMode === 'memory') return;
    const filtered = getFilteredQuestions();
    const q = filtered[currentIndex];

    if (selectedAnswers.size === 0) {
      alert('Please select at least one option.');
      return;
    }

    checkedCurrent = true;
    const btnVerify = document.getElementById('btn-verify');
    if (btnVerify) btnVerify.disabled = true;

    const correctSet = new Set(q.correct);
    const userArr = Array.from(selectedAnswers);
    const isCorrect = userArr.length === q.correct.length && userArr.every(ans => correctSet.has(ans));

    if (!userStats[q.id]) userStats[q.id] = { streak: 0, correct: 0, wrong: 0, mastered: false };

    if (isCorrect) {
      userStats[q.id].streak++;
      userStats[q.id].correct++;
      if (userStats[q.id].streak >= masteryThreshold) {
        userStats[q.id].mastered = true;
      }
    } else {
      userStats[q.id].streak = 0;
      userStats[q.id].wrong++;
      userStats[q.id].mastered = false;
    }

    saveStats();
    updateHeaderStats();

    // Visual feedback
    (q.options || []).forEach(opt => {
      const key = opt.letter || opt.key;
      const el = document.getElementById(`opt-${key}`);
      if (!el) return;

      if (correctSet.has(key)) {
        el.classList.add('correct-highlight');
      } else if (selectedAnswers.has(key)) {
        el.classList.add('wrong-highlight');
      }
    });

    // Show explanation
    const expArea = document.getElementById('explanation-area');
    if (expArea) {
      expArea.innerHTML = reviewExplanationMarkup(q);
      expArea.style.display = 'block';
    }
  }

  function prevQuestion() { moveQuestion(-1); }
  function nextQuestion() { moveQuestion(1); }

  function moveQuestion(direction) {
    const filtered = getFilteredQuestions();
    if (filtered.length <= 1) return;
    currentIndex += direction;
    if (currentIndex >= filtered.length) currentIndex = 0;
    if (currentIndex < 0) currentIndex = filtered.length - 1;
    renderCurrentQuestion();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function jumpToQuestion(e) {
    if (e) e.preventDefault();
    const jumpInputs = document.querySelectorAll('#question-jump-input');
    let val = '';
    jumpInputs.forEach(i => { if (i.value) val = i.value; });
    const targetId = parseInt(val, 10);

    const filtered = getFilteredQuestions();
    const idx = filtered.findIndex(q => q.id === targetId);

    if (idx !== -1) {
      currentIndex = idx;
      renderCurrentQuestion();
    } else {
      const foundInBank = ALL_QUESTIONS.some(q => q.id === targetId);
      const feedbackEls = document.querySelectorAll('.q-jump-feedback');
      feedbackEls.forEach(el => {
        el.textContent = foundInBank
          ? `Question #${targetId} is hidden by current filter.`
          : `Question #${targetId} does not exist (1-${ALL_QUESTIONS.length}).`;
      });
      setTimeout(() => feedbackEls.forEach(el => el.textContent = ''), 3500);
    }
  }

  function onSearch() {
    currentIndex = 0;
    renderCurrentQuestion();
  }

  function finishExam() {
    if (examTimerInterval) clearInterval(examTimerInterval);

    let correctCount = 0;
    const domainStats = {};

    examQuestions.forEach(q => {
      if (!domainStats[q.domain]) domainStats[q.domain] = { total: 0, correct: 0 };
      domainStats[q.domain].total++;

      const userAns = examAnswers[q.id] || [];
      const correctSet = new Set(q.correct);
      const isCorrect = userAns.length === q.correct.length && userAns.every(a => correctSet.has(a));

      if (isCorrect) {
        correctCount++;
        domainStats[q.domain].correct++;
      }
    });

    const pct = Math.round((correctCount / examQuestions.length) * 100);
    const passed = pct >= 65;

    let domSummary = Object.keys(domainStats).map(d => {
      const s = domainStats[d];
      return `<li><strong>${d.toUpperCase()}</strong>: ${s.correct} / ${s.total} (${Math.round((s.correct / s.total) * 100)}%)</li>`;
    }).join('');

    const container = document.getElementById('quiz-container');
    if (container) {
      container.innerHTML = `
        <div class="question-card" style="text-align:center; padding:30px;">
          <h2 style="color:${passed ? 'var(--success)' : 'var(--error)'}">${passed ? '🎉 PASSED!' : '❌ NOT PASSED'}</h2>
          <p style="font-size:1.2rem; margin:14px 0;">Final Score: <strong>${pct}%</strong> (Passing Threshold: 65%)</p>
          <p style="color:var(--text-muted); margin-bottom:20px;">Correct: ${correctCount} of ${examQuestions.length} questions</p>
          <div style="text-align:left; background:#0b1120; padding:16px; border-radius:8px; border:1px solid var(--border); max-width:420px; margin:0 auto 20px auto;">
            <h4 style="margin-bottom:8px; color:var(--accent);">Domain Breakdown:</h4>
            <ul style="padding-left:20px; font-size:0.9rem; line-height:1.6;">${domSummary}</ul>
          </div>
          <button class="primary" onclick="OracleApp.setMode('study')">Return to Study Mode</button>
        </div>
      `;
    }
  }

  function updateThreshold(val) {
    masteryThreshold = parseInt(val, 10);
    localStorage.setItem(config.thresholdKey, masteryThreshold);
    Object.keys(userStats).forEach(id => {
      if (userStats[id]) {
        userStats[id].mastered = userStats[id].streak >= masteryThreshold;
      }
    });
    saveStats();
    updateHeaderStats();
    renderCurrentQuestion();
  }

  function resetQuestionStreak(qid) {
    if (userStats[qid]) {
      userStats[qid].streak = 0;
      userStats[qid].mastered = false;
      saveStats();
      updateHeaderStats();
      renderCurrentQuestion();
    }
  }

  function openResetModal() {
    const m = document.getElementById('reset-modal');
    if (m) m.classList.add('active');
  }

  function closeResetModal() {
    const m = document.getElementById('reset-modal');
    if (m) m.classList.remove('active');
  }

  function buildResetModal() {
    const modalDomainsContainer = document.getElementById('modal-domains-list');
    if (!modalDomainsContainer) return;

    // Count true questions per domain dynamically
    const domainCounts = {};
    ALL_QUESTIONS.forEach(q => {
      const d = q.domain || 'general';
      domainCounts[d] = (domainCounts[d] || 0) + 1;
    });

    let html = '';
    Object.keys(domainCounts).sort().forEach(d => {
      html += `<button onclick="OracleApp.resetDomain('${d}')">Reset ${d.toUpperCase()} Domain (${domainCounts[d]} questions)</button>`;
    });
    html += `<button class="primary" onclick="OracleApp.resetAll()">⚠️ Reset ALL Progress</button>`;
    modalDomainsContainer.innerHTML = html;
  }

  function resetDomain(domain) {
    ALL_QUESTIONS.filter(q => q.domain === domain).forEach(q => {
      if (userStats[q.id]) {
        userStats[q.id].streak = 0;
        userStats[q.id].mastered = false;
      }
    });
    saveStats();
    updateHeaderStats();
    closeResetModal();
    renderCurrentQuestion();
    alert(`Streaks for domain '${domain.toUpperCase()}' reset to 0.`);
  }

  function resetAll() {
    if (confirm('Are you sure you want to reset all question streaks back to 0?')) {
      userStats = {};
      saveStats();
      updateHeaderStats();
      closeResetModal();
      renderCurrentQuestion();
    }
  }

  function saveStats() {
    localStorage.setItem(config.storageKey, JSON.stringify(userStats));
  }

  // Backup & Sync: Export / Import
  function exportProgress() {
    const data = {
      examId: config.examId,
      exportedAt: new Date().toISOString(),
      stats: userStats,
      threshold: masteryThreshold
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `oracle_${config.examId}_backup_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function importProgress(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.stats) {
          userStats = data.stats;
          saveStats();
          if (data.threshold) {
            masteryThreshold = data.threshold;
            localStorage.setItem(config.thresholdKey, masteryThreshold);
          }
          updateHeaderStats();
          renderCurrentQuestion();
          alert('Progress successfully imported!');
        } else {
          alert('Invalid backup file format.');
        }
      } catch (err) {
        alert('Error reading backup file: ' + err.message);
      }
    };
    reader.readAsText(file);
    fileInput.value = '';
  }

  // Text rendering & option reference helpers
  function escapeHtml(str) {
    return (str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function optionReference(letter) {
    return `<span class="option-ref" aria-label="Option ${letter}">${letter}</span>`;
  }

  function highlightOptionReferences(text) {
    const optionAVerbs = /^(?:is|are|was|were|does|doesn't|did|describes?|states?|says?|claims?|means?|refers?|confuses?|overstates?|misstates?|predicts?|assumes?|identifies?|matches?|contradicts?|requires?|allows?|cannot|can|fails?|succeeds?|applies|covers?|represents?|gives?|points?|omits?|provides?|lists?|includes?|uses?|creates?|returns?|shows?|depends?|indicates?|supports?|confirms?|suggests?|reverses?|reflects?|adds?|assigns?|places?|proposes?|makes?|limits?|synchronizes?|restricts?|drops?|invents?|mentions?|names?|converts?|recommends?|substitutes?|treats?|combines?|specifies|prescribes?|violates?|replaces?|eliminates?|qualifies|disregards?|presupposes?|overlooks?|ignores?|excludes?|follows?|must|should|isn't|aren't)\b/;

    return text.split(/(<[^>]+>)/g).map(part => {
      if (part.startsWith('<')) return part;
      return part.replace(/(?<![\w$*–-])[A-H](?![\w$*–-])/g, (letter, offset) => {
        if (letter !== 'A') return optionReference(letter);

        const before = part.slice(0, offset);
        const after = part.slice(offset + 1);
        const explicitReference = /\b(?:options?|choices?|answers?)\s+$/i.test(before);
        const referenceList = /[A-H]\s*(?:,\s*(?:and|or)?|and|or|\/|through)\s*$/.test(before);
        const referenceSuffix = /^\s*(?:[,.:)/]|['’]s\b|and\b|or\b|through\b)/.test(after);
        const quotedReference = /[“"‘']\s*$/.test(before) && /^["”’']/.test(after);
        const description = after.trimStart().replace(/^(?:incorrectly|wrongly|falsely|correctly|also|never|only|partially|similarly|already|properly)\s+/, '');

        if (explicitReference || referenceList || referenceSuffix || quotedReference ||
            optionAVerbs.test(description) || part.trim() === 'A') {
          return optionReference(letter);
        }
        return letter;
      });
    }).join('');
  }

  function renderExplanationText(text) {
    const rendered = escapeHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    return rendered.split(/(<code class="inline-code">[\s\S]*?<\/code>)/g)
      .map(part => part.startsWith('<code class="inline-code">') ? part : highlightOptionReferences(part))
      .join('')
      .replace(/\r?\n/g, '<br>');
  }

  function renderExplanation(text) {
    const source = String(text || '');
    const blockPattern = /```(?:sql|text|bash|shell)?\s*([\s\S]*?)```/gi;
    let html = '';
    let lastIndex = 0;
    let match;
    while ((match = blockPattern.exec(source)) !== null) {
      html += renderExplanationText(source.slice(lastIndex, match.index));
      html += `<pre class="explanation-code"><code>${escapeHtml(match[1].trim())}</code></pre>`;
      lastIndex = blockPattern.lastIndex;
    }
    html += renderExplanationText(source.slice(lastIndex));
    return html;
  }

  function reviewExplanationMarkup(q) {
    const note = q.review_note
      ? `<div class="review-note"><strong>Review Note</strong><br>${renderExplanationText(q.review_note)}</div>`
      : '';

    const refs = (q.sources || []).filter(ref => /^https:\/\/docs\.oracle\.com\//.test(ref.url));
    const links = refs.map(ref => `
      <a href="${escapeHtml(ref.url)}" target="_blank" rel="noopener noreferrer">
        🔗 ${escapeHtml(ref.title || 'Oracle 19c Documentation')}
      </a>
    `).join('');

    const docSection = links ? `<div class="oracle-reference"><strong>Oracle 19c Documentation</strong>${links}</div>` : '';

    return `
      <div class="explanation-box">
        <div class="explanation-title">💡 Detailed Explanation & Analysis</div>
        ${note}
        <div class="explanation-body">${renderExplanation(q.explanation)}</div>
        ${docSection}
      </div>
    `;
  }

  function renderQuestionBody(text) {
    if (!text) return '';
    const formatted = text.replace(/([.!?:])\s+(?=(?:Which|What|How|When|Where|Why|For which|Choose)\b[^?]*\?(?:\s*\(Choose[^)]*\))?\s*$)/i, '$1\n\n');
    const parts = formatted.split(/```(?:text|sql)?/g);
    let result = '';
    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 1) {
        result += '<pre class="code-block">' + escapeHtml(parts[i].trim()) + '</pre>';
      } else {
        result += escapeHtml(parts[i]);
      }
    }
    return result;
  }

  // Public API
  global.OracleApp = {
    init: initExamSimulator,
    setMode: setMode,
    toggleOption: toggleOption,
    verifyAnswer: verifyAnswer,
    prevQuestion: prevQuestion,
    nextQuestion: nextQuestion,
    jumpToQuestion: jumpToQuestion,
    onSearch: onSearch,
    finishExam: finishExam,
    updateThreshold: updateThreshold,
    resetQuestionStreak: resetQuestionStreak,
    openResetModal: openResetModal,
    closeResetModal: closeResetModal,
    resetDomain: resetDomain,
    resetAll: resetAll,
    exportProgress: exportProgress,
    importProgress: importProgress
  };

})(window);
