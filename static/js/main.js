// Client-side interactions - InterviewForge AI

document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    setupInterviewArena();
});

// ─── Drag and Drop File Upload ───────────────────────────────────────────────
function setupDragAndDrop() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('resume-file-input');
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent-primary)';
        dropzone.style.background  = 'rgba(99,102,241,0.05)';
    });
    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'var(--border-glass)';
        dropzone.style.background  = 'transparent';
    });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            document.getElementById('upload-form').submit();
        }
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) document.getElementById('upload-form').submit();
    });
}

// ─── Interview Arena State ───────────────────────────────────────────────────
let arenaTimer        = null;
let secondsRemaining  = 120;
let timeElapsed       = 0;
let currentSessionId  = null;
let currentQuestionId = null;

// Speech recognition state
let mic               = null;   // the SpeechRecognition instance
let micActive         = false;  // true while mic is open
let finalText         = '';     // committed words from finished utterances

// ─── Setup ───────────────────────────────────────────────────────────────────
function setupInterviewArena() {
    const arena = document.getElementById('interview-arena');
    if (!arena) return;

    currentSessionId = arena.dataset.sessionId;

    // Warm up mic permission immediately
    navigator.mediaDevices && navigator.mediaDevices.getUserMedia({ audio: true })
        .then(s => { s.getTracks().forEach(t => t.stop()); })
        .catch(() => {});

    // Voice-mode toggle
    const toggle = document.getElementById('voice-mode-toggle');
    if (toggle) {
        toggle.addEventListener('change', () => {
            if (!toggle.checked) stopMic();
        });
    }

    fetchNextQuestion();
}

// ─── Avatar + Status helpers ─────────────────────────────────────────────────
function setBotState(state) {
    const wrap = document.querySelector('.bot-wave-wrapper');
    const icon = document.getElementById('bot-icon');
    const ind  = document.getElementById('arena-status-indicator');
    if (!wrap) return;
    wrap.classList.remove('speaking-active', 'listening-active');
    if (state === 'speaking') {
        wrap.classList.add('speaking-active');
        if (icon) icon.innerText = '🗣️';
        if (ind)  { ind.style.display = 'inline-block'; ind.innerText = '● Bot speaking...'; ind.style.color = '#a78bfa'; }
    } else if (state === 'listening') {
        wrap.classList.add('listening-active');
        if (icon) icon.innerText = '🎙️';
        if (ind)  { ind.style.display = 'inline-block'; ind.innerText = '● Mic is live — speak now'; ind.style.color = '#fbbf24'; }
    } else {
        if (icon) icon.innerText = '🤖';
        if (ind)  ind.style.display = 'none';
    }
}

// ─── Fetch Next Question ─────────────────────────────────────────────────────
function fetchNextQuestion() {
    stopMic();
    window.speechSynthesis && window.speechSynthesis.cancel();
    clearInterval(arenaTimer);

    const questionTextEl  = document.getElementById('arena-question-text');
    const questionRoundEl = document.getElementById('arena-question-round');
    const diffLevelEl     = document.getElementById('arena-difficulty-level');
    const answerTextarea  = document.getElementById('arena-answer-text');
    const actionArea      = document.getElementById('arena-action-area');
    const skeleton        = document.getElementById('arena-skeleton');
    const feedbackPanel   = document.getElementById('evaluation-feedback-panel');

    answerTextarea.value        = '';
    answerTextarea.disabled     = false;
    feedbackPanel.style.display = 'none';
    skeleton.style.display      = 'block';
    setBotState('idle');
    finalText = '';

    fetch(`/interviews/api/${currentSessionId}/next-question/`)
        .then(r => r.json())
        .then(data => {
            skeleton.style.display = 'none';
            if (data.status === 'completed') { window.location.href = data.redirect_url; return; }

            questionTextEl.innerText  = data.question_text;
            questionRoundEl.innerText = `Round ${data.round} of 5`;
            diffLevelEl.innerText     = `Difficulty: ${data.difficulty_level}/10`;
            currentQuestionId         = data.question_id;

            const voiceOn = document.getElementById('voice-mode-toggle')?.checked;
            if (voiceOn) {
                speakQuestion(data.question_text, answerTextarea);
            } else {
                answerTextarea.placeholder = 'Type your answer here...';
                startTimer();
            }

            renderActionButtons(answerTextarea, voiceOn);
        })
        .catch(err => {
            skeleton.style.display   = 'none';
            questionTextEl.innerText = 'Failed to load question. Please refresh.';
            console.error(err);
        });
}

// ─── Render Action Buttons ───────────────────────────────────────────────────
function renderActionButtons(answerTextarea, voiceOn) {
    const actionArea = document.getElementById('arena-action-area');

    if (voiceOn) {
        // Show MIC BUTTON + Submit
        actionArea.innerHTML = `
            <div style="display:flex; gap:12px; justify-content:flex-end; align-items:center; flex-wrap:wrap;">
                <button id="mic-toggle-btn" style="
                    background: linear-gradient(135deg,#7c3aed,#6366f1);
                    border:none; border-radius:50px; padding:10px 22px;
                    color:#fff; font-size:14px; font-weight:600; cursor:pointer;
                    display:flex; align-items:center; gap:8px;
                    box-shadow: 0 0 20px rgba(99,102,241,0.4);
                    transition: all 0.2s;">
                    🎙️ Start Recording
                </button>
                <button id="submit-answer-btn" class="btn-primary">Submit Answer</button>
            </div>`;

        const micBtn = document.getElementById('mic-toggle-btn');
        micBtn.addEventListener('click', () => {
            if (micActive) {
                stopMic();
                micBtn.innerText = '🎙️ Start Recording';
                micBtn.style.background = 'linear-gradient(135deg,#7c3aed,#6366f1)';
                micBtn.style.boxShadow  = '0 0 20px rgba(99,102,241,0.4)';
                setBotState('idle');
            } else {
                startMic(answerTextarea);
                micBtn.innerHTML = '⏹ Stop Recording';
                micBtn.style.background = 'linear-gradient(135deg,#dc2626,#ef4444)';
                micBtn.style.boxShadow  = '0 0 20px rgba(239,68,68,0.5)';
                setBotState('listening');
            }
        });

    } else {
        actionArea.innerHTML = `<button id="submit-answer-btn" class="btn-primary">Submit Answer</button>`;
    }

    document.getElementById('submit-answer-btn').addEventListener('click', submitAnswer);
}

// ─── TTS: Speak the Question ─────────────────────────────────────────────────
function speakQuestion(text, textarea) {
    window.speechSynthesis.cancel();
    setBotState('speaking');
    textarea.disabled    = true;
    textarea.placeholder = 'Bot is reading the question...';

    const utter  = new SpeechSynthesisUtterance(text);
    utter.lang   = 'en-US';
    utter.rate   = 0.95;

    let done = false;
    function onDone() {
        if (done) return; done = true;
        textarea.disabled    = false;
        textarea.placeholder = '🎙️ Press "Start Recording" then speak your answer';
        textarea.focus();
        setBotState('idle');
        secondsRemaining = 120; timeElapsed = 0;
        startTimer();
    }

    utter.onend   = onDone;
    // Safety: if onend never fires (Chrome bug), kick off after estimated TTS time
    const safeMs  = Math.max(5000, text.split(' ').length * 85 + 2000);
    const fallback = setTimeout(onDone, safeMs);
    utter.onend   = () => { clearTimeout(fallback); onDone(); };

    window.speechSynthesis.speak(utter);
}

// ─── MIC: Start Listening ────────────────────────────────────────────────────
let keepListening = false;  // master flag — true while user wants mic on

function startMic(textarea) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        alert('Speech recognition is not supported.\nPlease open this site in Google Chrome or Microsoft Edge.');
        return;
    }

    // Kill any stale instance first
    if (mic) { try { mic.onend = null; mic.stop(); } catch(e){} mic = null; }

    keepListening = true;
    micActive     = true;
    finalText     = textarea.value.trim(); // keep existing typed text

    // Show subtitle bar
    const subBar     = document.getElementById('subtitle-bar');
    const subFinal   = document.getElementById('subtitle-final');
    const subInterim = document.getElementById('subtitle-interim');
    if (subBar)     subBar.style.display = 'block';
    if (subFinal)   subFinal.innerText   = finalText;
    if (subInterim) subInterim.innerText = '';

    _createAndStartMic(textarea, subFinal, subInterim, subBar);
}

function _createAndStartMic(textarea, subFinal, subInterim, subBar) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    mic = new SR();
    mic.continuous      = true;
    mic.interimResults  = true;
    mic.lang            = 'en-US';

    mic.onstart = () => {
        console.log('✅ Mic started — capturing audio');
        setBotState('listening');
    };

    mic.onspeechstart = () => console.log('🗣️ Speech detected');

    mic.onresult = (event) => {
        let interim  = '';
        let newFinal = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript;
            if (event.results[i].isFinal) { newFinal += t + ' '; }
            else { interim += t; }
        }
        if (newFinal) finalText += newFinal;

        const display = (finalText + interim).trim();
        if (display) textarea.value = display;

        // Live subtitles
        if (subFinal)   subFinal.innerText  = finalText;
        if (subInterim) subInterim.innerText = interim;
        if (subBar)     subBar.scrollTop = subBar.scrollHeight;
    };

    mic.onerror = (e) => {
        console.error('Mic error:', e.error);
        if (e.error === 'no-speech') return; // normal pause — ignore
        if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
            keepListening = false;
            micActive     = false;
            alert('🚫 Microphone blocked!\n\nFix: Click the lock icon in your browser address bar → Microphone → Allow → Refresh the page.');
            stopMic();
            setBotState('idle');
            const btn = document.getElementById('mic-toggle-btn');
            if (btn) { btn.innerHTML = '🎙️ Start Recording'; btn.style.background = 'linear-gradient(135deg,#7c3aed,#6366f1)'; }
            return;
        }
        if (e.error === 'network') {
            // Network error — Chrome speech API needs internet
            if (subInterim) subInterim.innerText = '⚠️ Network error — check internet connection';
            return;
        }
        console.warn('Unhandled error:', e.error);
    };

    // Recognition auto-ends after ~60 s or on pause: restart if keepListening
    mic.onend = () => {
        micActive = false;
        console.log('Mic ended. keepListening =', keepListening);
        if (keepListening) {
            setTimeout(() => {
                if (!keepListening) return;
                console.log('🔄 Restarting mic...');
                micActive = true;
                _createAndStartMic(textarea, subFinal, subInterim, subBar);
            }, 200);
        } else {
            setBotState('idle');
        }
    };

    try {
        mic.start();
        console.log('mic.start() called');
    } catch(e) {
        console.error('mic.start() threw:', e.message);
        micActive = false;
    }
}


// ─── MIC: Stop Listening ─────────────────────────────────────────────────────
function stopMic() {
    keepListening = false;
    micActive     = false;
    if (mic) {
        mic.onend   = null;
        mic.onerror = null;
        try { mic.stop(); } catch(e) {}
        mic = null;
    }
    // Hide subtitle bar, clear interim
    const subBar     = document.getElementById('subtitle-bar');
    const subInterim = document.getElementById('subtitle-interim');
    if (subInterim) subInterim.innerText = '';
    if (subBar) subBar.style.display = 'none';
}

// ─── Countdown Timer ─────────────────────────────────────────────────────────
function startTimer() {
    clearInterval(arenaTimer);
    const display = document.getElementById('arena-timer-display');
    arenaTimer = setInterval(() => {
        secondsRemaining--;
        timeElapsed++;
        const m = String(Math.floor(secondsRemaining / 60)).padStart(2,'0');
        const s = String(secondsRemaining % 60).padStart(2,'0');
        if (display) display.innerText = `Remaining: ${m}:${s}`;
        if (secondsRemaining <= 0) {
            clearInterval(arenaTimer);
            const ta = document.getElementById('arena-answer-text');
            if (ta && !ta.value.trim()) ta.value = 'No response within time limit.';
            submitAnswer();
        }
    }, 1000);
}

// ─── Submit Answer ────────────────────────────────────────────────────────────
function submitAnswer() {
    clearInterval(arenaTimer);
    stopMic();
    window.speechSynthesis && window.speechSynthesis.cancel();
    setBotState('idle');

    const textarea    = document.getElementById('arena-answer-text');
    const answerText  = textarea.value.trim();
    const feedPanel   = document.getElementById('evaluation-feedback-panel');
    const feedSkel    = document.getElementById('feedback-skeleton');

    if (!answerText) {
        alert('Please type or speak an answer before submitting.');
        return;
    }

    textarea.disabled       = true;
    feedPanel.style.display = 'block';
    feedSkel.style.display  = 'block';
    document.getElementById('feedback-real-content').style.display = 'none';

    fetch(`/interviews/api/${currentSessionId}/submit-answer/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            question_id: currentQuestionId,
            answer_text: answerText,
            response_time_seconds: timeElapsed
        })
    })
    .then(r => r.json())
    .then(data => {
        feedSkel.style.display = 'none';
        document.getElementById('feedback-real-content').style.display = 'block';

        document.getElementById('eval-score-overall').innerText       = data.scores.overall;
        document.getElementById('eval-score-technical').innerText     = data.scores.technical;
        document.getElementById('eval-score-communication').innerText = data.scores.communication;

        document.getElementById('eval-strengths-list').innerHTML  =
            data.strengths.map(s => `<li>${s}</li>`).join('');
        document.getElementById('eval-weaknesses-list').innerHTML =
            data.weaknesses.map(w => `<li>${w}</li>`).join('');
        document.getElementById('eval-missing-concepts').innerText =
            data.missing_concepts.length ? data.missing_concepts.join(', ') : 'None';
        document.getElementById('eval-ideal-answer').innerText = data.ideal_answer;

        const actionArea = document.getElementById('arena-action-area');
        actionArea.innerHTML = `<button id="next-question-btn" class="btn-primary">Next Question →</button>`;
        document.getElementById('next-question-btn').addEventListener('click', fetchNextQuestion);
    })
    .catch(err => {
        console.error(err);
        alert('Failed to submit. Please retry.');
        textarea.disabled       = false;
        feedPanel.style.display = 'none';
    });
}

// Backward-compatible alias used by old inline event listeners
function submitCandidateAnswer() { submitAnswer(); }
function stopSpeechRecognition() { stopMic(); }
function haltVoiceEngine()       { stopMic(); clearInterval(arenaTimer); }

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getCookie(name) {
    let v = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(c => {
            c = c.trim();
            if (c.startsWith(name + '=')) v = decodeURIComponent(c.slice(name.length + 1));
        });
    }
    return v;
}
