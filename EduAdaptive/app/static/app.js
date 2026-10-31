/**
 * EduAdaptive - Frontend Logic & Chart.js Visualizations
 * SDG 4 Quality Education Prototype - Pastel Theme & Login Flow
 */

// Application State
let currentStudent = null; // { id: number, name: string, persona: string }
let currentQuestion = null;
let selectedOption = null;
let recommendedQueue = [];
let masteryChartInstance = null;
let progressionChartInstance = null;
let masteryChartType = 'radar'; // 'radar' or 'bar'

// DOM Elements - Screens
const loginScreen = document.getElementById('loginScreen');
const appScreen = document.getElementById('appScreen');
const loginForm = document.getElementById('loginForm');
const inputStudentId = document.getElementById('inputStudentId');
const inputStudentName = document.getElementById('inputStudentName');
const loginSubmitBtn = document.getElementById('loginSubmitBtn');
const demoChips = document.querySelectorAll('.demo-chip');

// Header Profile Elements
const headerStudentName = document.getElementById('headerStudentName');
const headerStudentMeta = document.getElementById('headerStudentMeta');
const logoutBtn = document.getElementById('logoutBtn');
const resetBtn = document.getElementById('resetBtn');
const liveStudentBadge = document.getElementById('liveStudentBadge');

// Tabs
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Practice Mode Elements
const questionCard = document.getElementById('questionCard');
const loadingQuestion = document.getElementById('loadingQuestion');
const qTopicBadge = document.getElementById('qTopicBadge');
const qDifficultyBadge = document.getElementById('qDifficultyBadge');
const qZpdBadge = document.getElementById('qZpdBadge');
const qSuccessProb = document.getElementById('qSuccessProb');
const qReasoningText = document.getElementById('qReasoningText');
const qText = document.getElementById('qText');
const optionsList = document.getElementById('optionsList');
const selectionHint = document.getElementById('selectionHint');
const submitAnswerBtn = document.getElementById('submitAnswerBtn');
const feedbackPanel = document.getElementById('feedbackPanel');
const feedbackTitle = document.getElementById('feedbackTitle');
const feedbackExplanation = document.getElementById('feedbackExplanation');
const diffTopicName = document.getElementById('diffTopicName');
const diffOldVal = document.getElementById('diffOldVal');
const diffNewVal = document.getElementById('diffNewVal');
const diffDeltaPill = document.getElementById('diffDeltaPill');
const nextQuestionBtn = document.getElementById('nextQuestionBtn');
const recommendationQueue = document.getElementById('recommendationQueue');
const quickMasteryBars = document.getElementById('quickMasteryBars');

// Dashboard Elements
const kpiOverallMastery = document.getElementById('kpiOverallMastery');
const kpiTotalAttempts = document.getElementById('kpiTotalAttempts');
const kpiAccuracyRate = document.getElementById('kpiAccuracyRate');
const kpiFocusTopic = document.getElementById('kpiFocusTopic');
const chartTypeRadar = document.getElementById('chartTypeRadar');
const chartTypeBar = document.getElementById('chartTypeBar');
const attemptHistoryBody = document.getElementById('attemptHistoryBody');
const toastContainer = document.getElementById('toastContainer');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  initLoginFlow();
  initTabs();
  initChartToggles();
  initPracticeEvents();
  checkExistingSession();
});

// Toast notification helper
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : 'ℹ'}</span> <span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --- Login Flow ---
function initLoginFlow() {
  // Demo chip auto-fills
  demoChips.forEach(chip => {
    chip.addEventListener('click', () => {
      inputStudentId.value = chip.getAttribute('data-id');
      inputStudentName.value = chip.getAttribute('data-name');
    });
  });

  // Login form submission
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const idVal = parseInt(inputStudentId.value.trim(), 10);
    const nameVal = inputStudentName.value.trim();

    if (!idVal || !nameVal) {
      showToast('Please provide both Student ID and Name.', 'error');
      return;
    }

    loginSubmitBtn.disabled = true;
    loginSubmitBtn.textContent = 'Logging in...';

    try {
      const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: idVal, name: nameVal })
      });

      if (!res.ok) {
        throw new Error(`Login failed (HTTP ${res.status})`);
      }

      const data = await res.json();
      currentStudent = {
        id: data.student_id,
        name: data.name,
        persona: data.persona
      };

      // Save to localStorage for page persistence
      localStorage.setItem('edu_student', JSON.stringify(currentStudent));

      showToast(data.message, 'success');
      launchAppScreen();
    } catch (err) {
      showToast('Login error: ' + err.message, 'error');
    } finally {
      loginSubmitBtn.disabled = false;
      loginSubmitBtn.textContent = 'Start Practicing ➔';
    }
  });

  // Switch student / Log out
  logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('edu_student');
    currentStudent = null;
    appScreen.style.display = 'none';
    loginScreen.style.display = 'flex';
    inputStudentId.value = '';
    inputStudentName.value = '';
    showToast('Logged out. Choose or enter a student to begin.', 'info');
  });

  // Scoped reset for current student
  resetBtn.addEventListener('click', async () => {
    if (!currentStudent) return;
    if (confirm(`Reset practice history and mastery state for ${currentStudent.name} (ID: ${currentStudent.id})?`)) {
      resetBtn.disabled = true;
      resetBtn.textContent = 'Resetting...';
      try {
        const res = await fetch(`/reset?student_id=${currentStudent.id}`, { method: 'POST' });
        if (res.ok) {
          showToast(`Practice data for ${currentStudent.name} reset!`, 'success');
          await refreshAllViews();
        } else {
          showToast('Failed to reset student data.', 'error');
        }
      } catch (err) {
        showToast('Error resetting: ' + err.message, 'error');
      } finally {
        resetBtn.disabled = false;
        resetBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          Reset My Data
        `;
      }
    }
  });
}

function checkExistingSession() {
  const saved = localStorage.getItem('edu_student');
  if (saved) {
    try {
      currentStudent = JSON.parse(saved);
      launchAppScreen();
    } catch (e) {
      localStorage.removeItem('edu_student');
    }
  }
}

async function launchAppScreen() {
  loginScreen.style.display = 'none';
  appScreen.style.display = 'block';

  // Update header info
  headerStudentName.textContent = currentStudent.name;
  headerStudentMeta.textContent = `ID: ${currentStudent.id} • ${currentStudent.persona}`;
  liveStudentBadge.textContent = `${currentStudent.name} (ID: ${currentStudent.id})`;

  // Switch to Practice Tab by default
  switchTab('practice-tab');
  await refreshAllViews();
}

// Tab navigation
function initTabs() {
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(targetTab) {
  tabButtons.forEach(b => b.classList.remove('active'));
  tabContents.forEach(c => c.classList.remove('active'));

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${targetTab}"]`);
  if (activeBtn) activeBtn.classList.add('active');

  const activeContent = document.getElementById(targetTab);
  if (activeContent) activeContent.classList.add('active');

  if (targetTab === 'dashboard-tab') {
    loadDashboardData();
  }
}

function initChartToggles() {
  chartTypeRadar.addEventListener('click', () => {
    masteryChartType = 'radar';
    chartTypeRadar.classList.add('active');
    chartTypeBar.classList.remove('active');
    loadDashboardData();
  });

  chartTypeBar.addEventListener('click', () => {
    masteryChartType = 'bar';
    chartTypeBar.classList.add('active');
    chartTypeRadar.classList.remove('active');
    loadDashboardData();
  });
}

function initPracticeEvents() {
  submitAnswerBtn.addEventListener('click', submitAnswer);

  nextQuestionBtn.addEventListener('click', () => {
    feedbackPanel.style.display = 'none';
    submitAnswerBtn.disabled = true;
    submitAnswerBtn.style.display = 'inline-flex';
    submitAnswerBtn.textContent = 'Submit Answer';
    selectionHint.textContent = 'Select an answer above';
    loadRecommendations();
  });
}

async function refreshAllViews() {
  feedbackPanel.style.display = 'none';
  selectedOption = null;
  submitAnswerBtn.disabled = true;
  submitAnswerBtn.style.display = 'inline-flex';
  submitAnswerBtn.textContent = 'Submit Answer';
  await Promise.all([loadRecommendations(), loadDashboardData()]);
}

// --- Practice Mode Handlers ---

async function loadRecommendations() {
  if (!currentStudent) return;
  loadingQuestion.style.display = 'block';
  questionCard.style.display = 'none';

  try {
    const res = await fetch(`/next-questions/${currentStudent.id}?count=4`);
    recommendedQueue = await res.json();

    if (recommendedQueue.length === 0) {
      qText.textContent = 'No more questions available in this session!';
      return;
    }

    currentQuestion = recommendedQueue[0];
    renderActiveQuestion(currentQuestion);
    renderQueue(recommendedQueue.slice(1));
  } catch (err) {
    showToast('Failed to load recommendations: ' + err.message, 'error');
  } finally {
    loadingQuestion.style.display = 'none';
    questionCard.style.display = 'block';
  }
}

function renderActiveQuestion(q) {
  selectedOption = null;
  submitAnswerBtn.disabled = true;

  qTopicBadge.textContent = q.topic;
  qTopicBadge.setAttribute('data-topic', q.topic);
  qDifficultyBadge.textContent = `Difficulty ${q.difficulty}/5`;
  qZpdBadge.style.display = q.target_zpd ? 'inline-flex' : 'none';

  const probPct = Math.round(q.predicted_success_prob * 100);
  qSuccessProb.textContent = `Predicted Success: ${probPct}%`;
  qReasoningText.textContent = q.reasoning;
  qText.textContent = q.question_text;

  // Options
  optionsList.innerHTML = '';
  const optionKeys = ['A', 'B', 'C', 'D'];

  q.options.forEach((optText, idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'option-btn';
    btn.setAttribute('data-value', optText);
    btn.innerHTML = `
      <span class="option-key">${optionKeys[idx] || idx + 1}</span>
      <span class="option-label">${optText}</span>
    `;

    btn.addEventListener('click', () => {
      document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedOption = optText;
      submitAnswerBtn.disabled = false;
      selectionHint.textContent = `Selected: "${optText}"`;
    });

    optionsList.appendChild(btn);
  });
}

function renderQueue(upcoming) {
  recommendationQueue.innerHTML = '';
  if (upcoming.length === 0) {
    recommendationQueue.innerHTML = '<p class="queue-reason">Queue is fully caught up!</p>';
    return;
  }

  upcoming.forEach(item => {
    const el = document.createElement('div');
    el.className = 'queue-item';
    const probPct = Math.round(item.predicted_success_prob * 100);
    el.innerHTML = `
      <div class="queue-item-header">
        <span class="badge topic-badge" data-topic="${item.topic}">${item.topic}</span>
        <span class="badge diff-badge">Lv ${item.difficulty}</span>
      </div>
      <div class="queue-q-text" title="${item.question_text}">${item.question_text}</div>
      <div class="queue-reason">${item.reasoning} (${probPct}% predicted)</div>
    `;
    recommendationQueue.appendChild(el);
  });
}

async function submitAnswer() {
  if (!currentQuestion || !selectedOption || !currentStudent) return;

  submitAnswerBtn.disabled = true;
  submitAnswerBtn.textContent = 'Evaluating with ML...';

  try {
    const payload = {
      student_id: currentStudent.id,
      question_id: currentQuestion.id,
      selected_option: selectedOption
    };

    const res = await fetch('/attempt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    displayFeedback(data);

    // Refresh background stats
    loadDashboardData();
  } catch (err) {
    showToast('Failed to submit answer: ' + err.message, 'error');
    submitAnswerBtn.disabled = false;
    submitAnswerBtn.textContent = 'Submit Answer';
  }
}

function displayFeedback(data) {
  submitAnswerBtn.style.display = 'none';

  // Highlight options
  const optionButtons = document.querySelectorAll('.option-btn');
  optionButtons.forEach(btn => {
    const val = btn.getAttribute('data-value');
    btn.disabled = true;
    if (val.trim() === data.correct_answer.trim()) {
      btn.classList.add('correct-highlight');
    } else if (val.trim() === data.selected_option.trim() && !data.is_correct) {
      btn.classList.add('wrong-highlight');
    }
  });

  // Feedback panel
  feedbackPanel.style.display = 'block';
  feedbackPanel.className = `feedback-panel ${data.is_correct ? 'correct' : 'incorrect'}`;

  const iconEl = document.getElementById('feedbackIcon');
  if (data.is_correct) {
    iconEl.textContent = '✓';
    feedbackTitle.textContent = 'Correct Answer! 🎉';
  } else {
    iconEl.textContent = '✗';
    feedbackTitle.textContent = `Incorrect. Correct answer was: ${data.correct_answer}`;
  }

  feedbackExplanation.textContent = `${data.explanation} ${data.feedback_message}`;

  // Mastery visual diff
  diffTopicName.textContent = data.topic;
  const oldPct = Math.round(data.previous_mastery * 100);
  const newPct = Math.round(data.updated_mastery * 100);
  const deltaPct = Math.round(data.mastery_delta * 100);

  diffOldVal.textContent = `${oldPct}%`;
  diffNewVal.textContent = `${newPct}%`;

  if (deltaPct > 0) {
    diffDeltaPill.className = 'badge diff-delta-pill positive';
    diffDeltaPill.textContent = `+${deltaPct}%`;
  } else if (deltaPct < 0) {
    diffDeltaPill.className = 'badge diff-delta-pill negative';
    diffDeltaPill.textContent = `${deltaPct}%`;
  } else {
    diffDeltaPill.className = 'badge diff-delta-pill neutral';
    diffDeltaPill.textContent = `0%`;
  }
}

// --- Dashboard & Analytics Handlers ---

async function loadDashboardData() {
  if (!currentStudent) return;
  try {
    const res = await fetch(`/dashboard/${currentStudent.id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // 1. KPI Cards
    kpiOverallMastery.textContent = `${Math.round(data.overall_mastery * 100)}%`;
    kpiTotalAttempts.textContent = data.total_attempts;
    kpiAccuracyRate.textContent = `${Math.round(data.overall_accuracy * 100)}%`;
    kpiFocusTopic.textContent = data.focus_topic;

    // 2. Quick Mastery Bars
    renderQuickBars(data.topic_mastery);

    // 3. Mastery Chart (Radar or Bar) with Pastel Palette
    renderMasteryChart(data.topic_mastery);

    // 4. Progression Timeline Chart with Pastel Palette
    renderProgressionChart(data.difficulty_timeline);

    // 5. History Table
    renderHistoryTable(data.recent_attempts);
  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderQuickBars(topicMasteries) {
  quickMasteryBars.innerHTML = '';
  topicMasteries.forEach(tm => {
    const pct = Math.round(tm.mastery_score * 100);
    const row = document.createElement('div');
    row.innerHTML = `
      <div class="bar-row-label">
        <span>${tm.topic}</span>
        <span>${pct}% (Lv ${tm.last_difficulty})</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${pct}%"></div>
      </div>
    `;
    quickMasteryBars.appendChild(row);
  });
}

function renderMasteryChart(topicMasteries) {
  const ctx = document.getElementById('masteryChart').getContext('2d');
  const labels = topicMasteries.map(t => t.topic);
  const dataValues = topicMasteries.map(t => Math.round(t.mastery_score * 100));

  if (masteryChartInstance) {
    masteryChartInstance.destroy();
  }

  if (masteryChartType === 'radar') {
    masteryChartInstance = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Current Mastery (%)',
            data: dataValues,
            fill: true,
            backgroundColor: 'rgba(201, 184, 232, 0.45)', // Soft Lavender Fill
            borderColor: '#8A6FA8',
            pointBackgroundColor: '#634982',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#634982',
            pointRadius: 4,
            borderWidth: 2
          },
          {
            label: 'Proficiency Target (80%)',
            data: labels.map(() => 80),
            borderColor: 'rgba(184, 232, 212, 0.85)', // Mint Green Benchmark
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            angleLines: { color: '#EAE6F4' },
            grid: { color: '#F3F1F8' },
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: { stepSize: 20, font: { size: 10, family: 'Inter' } },
            pointLabels: { font: { size: 11, family: 'Poppins', weight: '600' }, color: '#3A3A4A' }
          }
        },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } } }
        }
      }
    });
  } else {
    // Pastel Bar Chart
    masteryChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Current Mastery (%)',
            data: dataValues,
            backgroundColor: [
              '#A8D8EA', // Soft Blue (Algebra)
              '#B8E8D4', // Mint Green (Geometry)
              '#C9B8E8', // Lavender (Probability)
              '#FFD3B6'  // Peach (Number Systems)
            ],
            borderColor: [
              '#75b4c9',
              '#8ec2ac',
              '#a794c9',
              '#e0a984'
            ],
            borderWidth: 1.5,
            borderRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: v => v + '%', font: { family: 'Inter' } },
            grid: { color: '#F3F1F8' }
          },
          x: {
            ticks: { font: { family: 'Poppins', weight: '600' } },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}

function renderProgressionChart(timeline) {
  const ctx = document.getElementById('progressionChart').getContext('2d');

  if (progressionChartInstance) {
    progressionChartInstance.destroy();
  }

  if (!timeline || timeline.length === 0) {
    return;
  }

  const recentTimeline = timeline.slice(-25);
  const labels = recentTimeline.map(t => `#${t.attempt_number}`);
  const difficulties = recentTimeline.map(t => t.difficulty);
  // Mint green for correct, soft coral/peach for incorrect
  const pointColors = recentTimeline.map(t => (t.is_correct ? '#B8E8D4' : '#FFAAA6'));
  const pointBorderColors = recentTimeline.map(t => (t.is_correct ? '#1B5842' : '#8C2C28'));

  progressionChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Question Difficulty',
          data: difficulties,
          borderColor: '#C9B8E8', // Pastel Lavender connecting line
          borderWidth: 2.5,
          tension: 0.25,
          pointBackgroundColor: pointColors,
          pointBorderColor: pointBorderColors,
          pointBorderWidth: 1.5,
          pointRadius: 5.5,
          pointHoverRadius: 7.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 1,
          max: 5,
          ticks: {
            stepSize: 1,
            callback: v => `Lv ${v}`,
            font: { family: 'Inter' }
          },
          grid: { color: '#F3F1F8' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Inter' } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items[0].dataIndex;
              const att = recentTimeline[idx];
              return `Attempt #${att.attempt_number} • ${att.topic}`;
            },
            label: (item) => {
              const att = recentTimeline[item.dataIndex];
              const status = att.is_correct ? 'Correct (✓)' : 'Incorrect (✗)';
              return `Difficulty: Level ${att.difficulty} [${status}]`;
            },
            afterLabel: (item) => {
              const att = recentTimeline[item.dataIndex];
              return `Rolling Accuracy: ${Math.round(att.rolling_accuracy * 100)}%`;
            }
          }
        }
      }
    }
  });
}

function renderHistoryTable(attempts) {
  attemptHistoryBody.innerHTML = '';
  if (!attempts || attempts.length === 0) {
    attemptHistoryBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:var(--charcoal-muted);">No attempts recorded yet. Start practicing to generate history!</td></tr>';
    return;
  }

  attempts.forEach((a) => {
    const tr = document.createElement('tr');
    const outcomeBadge = a.is_correct
      ? '<span class="pill-success">Correct</span>'
      : '<span class="pill-fail">Incorrect</span>';

    let timeStr = a.timestamp;
    try {
      const d = new Date(a.timestamp);
      timeStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {}

    tr.innerHTML = `
      <td><strong>#${a.id}</strong></td>
      <td><span class="badge topic-badge" data-topic="${a.topic}">${a.topic}</span></td>
      <td><span class="badge diff-badge">Level ${a.difficulty}</span></td>
      <td>${outcomeBadge}</td>
      <td title="${a.question_text || ''}">${(a.question_text || '').substring(0, 45)}...</td>
      <td style="color:var(--charcoal-muted); font-size:0.75rem;">${timeStr}</td>
    `;
    attemptHistoryBody.appendChild(tr);
  });
}
