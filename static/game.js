/* ═══════════════════════════════════════════════════════════
   AI TRIBUNAL — Game Logic
   Connects to the session-aware FastAPI game endpoints
   ═══════════════════════════════════════════════════════════ */

const BASE = window.location.origin;
let currentAction = "examine_evidence";
let gameState = null;
let isDone = false;
let gameSessionId = null;
let coJudgeRemainingHints = 0;
const TOUR_STORAGE_KEY = "ai-tribunal-tour-seen";
const TOUR_STEPS = [
    {
        anchor: ".parties-panel",
        title: "Read both sides first",
        body: "Start by comparing the plaintiff and defendant stories. The job is not to trust the loudest side, but to notice where the stories stop lining up.",
        tip: "Use the manipulation panel as a warning system. It should make you curious, not replace your reasoning."
    },
    {
        anchor: ".evidence-board",
        title: "Treat evidence like a forensic board",
        body: "Click any evidence card to target it. High credibility does not guarantee truth, and low credibility does not automatically mean fabrication.",
        tip: "A good first move is usually to inspect the evidence item that feels too convenient, too late, or too polished."
    },
    {
        anchor: ".action-panel",
        title: "Choose the right courtroom move",
        body: "Use Examine to inspect materials, question either side when their story has gaps, and use RULE only when you can clearly justify the verdict in writing.",
        tip: "If you are unsure what to do next, follow the Judge Playbook in the action panel."
    },
    {
        anchor: ".hud-center",
        title: "Watch the score and step budget",
        body: "You have limited steps. The HUD shows how far you are into the hearing, how your total score is evolving, and whether your ruling stays consistent with earlier cases in the same session.",
        tip: "Do not spend every move. The best hearing is decisive, not noisy."
    },
    {
        anchor: "#btn-submit",
        title: "Submit with intent",
        body: "Every action should have a target or a written reason that explains what you are testing. When you switch to RULE, write the judgment like you would defend it on appeal.",
        tip: "You can reopen this guide any time with the help button in the top-right corner."
    }
];
const ACTION_GUIDANCE = {
    examine_evidence: {
        title: "Start with Examine",
        body: "Click an evidence card to auto-fill the target box, then explain what looks suspicious, inconsistent, or surprisingly strong."
    },
    question_plaintiff: {
        title: "Use this when the plaintiff story has gaps",
        body: "Ask the plaintiff when dates, receipts, timelines, or claimed damages do not fully connect to the evidence on the board."
    },
    question_defendant: {
        title: "Use this when the defense feels evasive",
        body: "Question the defendant when a policy, inspection, or internal record looks manufactured, incomplete, or strategically timed."
    },
    rule: {
        title: "Rule only when you can defend it",
        body: "Select the verdict only after you have tested the suspicious evidence. The judgment text should explain why your ruling survives scrutiny."
    }
};
let tourStepIndex = 0;
let highlightedTourElement = null;

function hasSeenTour() {
    try {
        return window.localStorage.getItem(TOUR_STORAGE_KEY) === "true";
    } catch (_err) {
        return false;
    }
}

function markTourSeen() {
    try {
        window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
    } catch (_err) {
        // Ignore storage failures and keep the tour usable.
    }
}

function clearTourHighlight() {
    if (highlightedTourElement) {
        highlightedTourElement.classList.remove("tour-focus");
        highlightedTourElement = null;
    }
}

function applyTourHighlight(selector) {
    clearTourHighlight();
    if (!selector) return;

    const target = document.querySelector(selector);
    if (!target) return;

    highlightedTourElement = target;
    highlightedTourElement.classList.add("tour-focus");
    highlightedTourElement.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
}

function renderTour() {
    const step = TOUR_STEPS[tourStepIndex];
    if (!step) return;

    document.getElementById("tour-progress").textContent = `Step ${tourStepIndex + 1} of ${TOUR_STEPS.length}`;
    document.getElementById("tour-title").textContent = step.title;
    document.getElementById("tour-body").textContent = step.body;
    document.getElementById("tour-tip").textContent = step.tip;
    document.getElementById("tour-prev").disabled = tourStepIndex === 0;
    document.getElementById("tour-next").textContent = tourStepIndex === TOUR_STEPS.length - 1 ? "Finish" : "Next";

    applyTourHighlight(step.anchor);
}

function openTour(stepIndex = 0) {
    const overlay = document.getElementById("tour-overlay");
    if (!overlay) return;

    tourStepIndex = Math.max(0, Math.min(stepIndex, TOUR_STEPS.length - 1));
    overlay.classList.remove("hidden");
    renderTour();
}

function closeTour() {
    const overlay = document.getElementById("tour-overlay");
    if (overlay) {
        overlay.classList.add("hidden");
    }
    clearTourHighlight();
    markTourSeen();
}

function nextTourStep() {
    if (tourStepIndex >= TOUR_STEPS.length - 1) {
        closeTour();
        return;
    }
    tourStepIndex += 1;
    renderTour();
}

function prevTourStep() {
    if (tourStepIndex === 0) return;
    tourStepIndex -= 1;
    renderTour();
}

function maybeOpenTour() {
    if (!hasSeenTour()) {
        openTour(0);
    }
}

function refreshTourHighlight() {
    const overlay = document.getElementById("tour-overlay");
    if (!overlay || overlay.classList.contains("hidden")) return;
    renderTour();
}

function updateActionGuidance(action = currentAction) {
    const guidance = ACTION_GUIDANCE[action] || ACTION_GUIDANCE.examine_evidence;
    const title = document.getElementById("action-guidance-title");
    const body = document.getElementById("action-guidance-text");
    if (!title || !body) return;
    title.textContent = guidance.title;
    body.textContent = guidance.body;
}

function resetActionComposer() {
    currentAction = "examine_evidence";
    document.querySelectorAll(".action-type-btn").forEach(btn => btn.classList.remove("active"));

    const examineButton = document.querySelector('.action-type-btn[data-action="examine_evidence"]');
    if (examineButton) {
        examineButton.classList.add("active");
    }

    document.getElementById("verdict-section").classList.add("hidden");
    document.getElementById("inp-target").value = "";
    document.getElementById("inp-reasoning").value = "";
    document.getElementById("inp-verdict-reasoning").value = "";
    updateActionGuidance();
}

function updateCoJudgeSummary() {
    const remaining = document.getElementById("cojudge-remaining");
    const button = document.getElementById("btn-cojudge");
    if (!remaining || !button) return;

    const hintLabel = `${coJudgeRemainingHints} hint${coJudgeRemainingHints === 1 ? "" : "s"} left`;
    remaining.textContent = hintLabel;
    button.disabled = isDone || coJudgeRemainingHints <= 0 || !gameSessionId;
}

function showCoJudgeResult(message, suggestion = null) {
    const box = document.getElementById("cojudge-box");
    const status = document.getElementById("cojudge-status");
    const action = document.getElementById("cojudge-action");
    const why = document.getElementById("cojudge-why");
    const watch = document.getElementById("cojudge-watch");
    const draft = document.getElementById("cojudge-draft");
    if (!box || !status || !action || !why || !watch || !draft) return;

    status.textContent = message || "";
    if (!suggestion) {
        action.textContent = "";
        why.textContent = "";
        watch.innerHTML = "";
        draft.textContent = "";
        if (message) {
            box.classList.remove("hidden");
        } else {
            box.classList.add("hidden");
        }
        return;
    }

    const verdictSuffix = suggestion.recommended_verdict ? ` -> ${suggestion.recommended_verdict}` : "";
    action.textContent = `Suggested next move: ${suggestion.recommended_action_type}${suggestion.target ? ` (${suggestion.target})` : ""}${verdictSuffix}`;
    why.textContent = suggestion.why_now || "";

    watch.innerHTML = "";
    (suggestion.watch_for || []).forEach((item) => {
        const chip = document.createElement("span");
        chip.className = "cojudge-chip";
        chip.textContent = item;
        watch.appendChild(chip);
    });

    draft.textContent = suggestion.draft_reasoning || "";
    box.classList.remove("hidden");
}

async function askCoJudge() {
    if (!gameSessionId || isDone) return;

    const button = document.getElementById("btn-cojudge");
    if (!button) return;
    button.disabled = true;
    button.textContent = "Consulting...";

    try {
        const res = await fetch(`${BASE}/game/cojudge`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: gameSessionId }),
        });
        const data = await res.json();
        coJudgeRemainingHints = data.remaining_hints ?? coJudgeRemainingHints;
        updateCoJudgeSummary();
        showCoJudgeResult(data.message || "AI Co-Judge updated.", data.suggestion || null);
    } catch (err) {
        showCoJudgeResult(`AI Co-Judge request failed: ${err.message}`);
    } finally {
        button.textContent = "Ask AI Co-Judge";
        updateCoJudgeSummary();
    }
}

// ─── SPLASH → GAME ─────────────────────────────────────────
async function startCase(level) {
    const btn = document.querySelector(`.case-btn[data-level="${level}"]`);
    btn.style.transform = "scale(0.95)";
    btn.style.opacity = "0.7";

    try {
        const res = await fetch(`${BASE}/game/reset`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_level: level }),
        });
        const data = await res.json();
        gameSessionId = data.session_id || null;
        gameState = data.observation || data;
        coJudgeRemainingHints = data.ai_judge?.calls_remaining ?? 0;
        isDone = false;
        resetActionComposer();
        document.getElementById("splash").classList.add("hidden");
        document.getElementById("game").classList.remove("hidden");
        renderGame();
        showCoJudgeResult("", null);
        updateCoJudgeSummary();
        maybeOpenTour();
    } catch (err) {
        alert("Could not connect to the environment server. Make sure it's running!");
        console.error(err);
    } finally {
        btn.style.transform = "";
        btn.style.opacity = "";
    }
}

// ─── RANDOM / GENERATED CASE ───────────────────────────────
async function startRandomCase(level) {
    const allBtns = document.querySelectorAll(".case-btn");
    allBtns.forEach(b => { b.disabled = true; b.style.opacity = "0.6"; });

    try {
        const res = await fetch(`${BASE}/game/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level }),
        });
        const data = await res.json();
        if (data.error) { alert("Generator error: " + data.error); return; }
        gameSessionId = data.session_id;
        gameState = data.observation;
        coJudgeRemainingHints = data.ai_judge?.calls_remaining ?? 0;
        isDone = false;
        resetActionComposer();
        document.getElementById("splash").classList.add("hidden");
        document.getElementById("game").classList.remove("hidden");
        renderGame();
        showCoJudgeResult("", null);
        updateCoJudgeSummary();
        maybeOpenTour();
    } catch (err) {
        alert("Could not generate case: " + err.message);
        console.error(err);
    } finally {
        allBtns.forEach(b => { b.disabled = false; b.style.opacity = ""; });
    }
}

function backToSplash() {
    closeTour();
    document.getElementById("game").classList.add("hidden");
    document.getElementById("splash").classList.remove("hidden");
    document.getElementById("log-entries").innerHTML = '<div class="log-empty">Your hearing history will appear here after the first action.</div>';
    isDone = false;
    gameState = null;
    gameSessionId = null;
    coJudgeRemainingHints = 0;
    showCoJudgeResult("", null);
}

// ─── RENDER GAME STATE ──────────────────────────────────────
function renderGame() {
    const obs = gameState;

    // HUD
    document.getElementById("hud-step").textContent = `${obs.time_step || 0}/${obs.max_steps || "?"}`;
    document.getElementById("hud-score").textContent = (obs.cumulative_score || 0).toFixed(3);
    document.getElementById("hud-consistency").textContent = (obs.consistency_score || 1).toFixed(2);
    document.getElementById("hud-title").textContent = obs.case_title || "AI TRIBUNAL";

    // Parties
    document.getElementById("plaintiff-name").textContent = obs.case_title ? obs.case_title.split(" vs ")[0] : "Plaintiff";
    document.getElementById("plaintiff-statement").textContent = obs.plaintiff_statement || "";
    document.getElementById("defendant-name").textContent = obs.case_title ? (obs.case_title.split(" vs ")[1] || "Defendant") : "Defendant";
    document.getElementById("defendant-statement").textContent = obs.defendant_statement || "";

    // Evidence
    const grid = document.getElementById("evidence-grid");
    grid.innerHTML = "";
    (obs.evidence_items || []).forEach(ev => {
        const cred = ev.credibility_score || 0.5;
        let credColor;
        if (cred >= 0.8) credColor = "#2ecc71";
        else if (cred >= 0.5) credColor = "#f39c12";
        else credColor = "#e74c3c";

        const card = document.createElement("div");
        card.className = "evidence-card";
        card.onclick = () => {
            document.getElementById("inp-target").value = ev.evidence_id;
            document.querySelectorAll(".evidence-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
        };
        card.innerHTML = `
            <div class="ev-header">
                <span class="ev-id">${ev.evidence_type === "document" ? "📄" : "🗣️"} ${ev.evidence_id}</span>
                <span class="ev-by ${ev.submitted_by === "plaintiff" ? "plaintiff-ev" : "defendant-ev"}">
                    ${ev.submitted_by === "plaintiff" ? "🔵 PLT" : "🔴 DEF"}
                </span>
            </div>
            <div class="ev-desc">${(ev.description || "").substring(0, 100)}${(ev.description || "").length > 100 ? "..." : ""}</div>
            <div class="ev-cred-bar">
                <div class="ev-cred-fill" style="width:${cred * 100}%; background:${credColor};"></div>
            </div>
            <div class="ev-cred-label">Credibility: ${(cred * 100).toFixed(0)}%</div>
        `;
        grid.appendChild(card);
    });

    // Manipulation signals
    const manipList = document.getElementById("manip-list");
    const manipSignals = obs.manipulative_signals || [];
    manipList.innerHTML = "";
    manipSignals.forEach(s => {
        const div = document.createElement("div");
        div.className = "manip-item";
        div.textContent = "⚠️ " + s;
        manipList.appendChild(div);
    });
    if (!manipSignals.length) {
        const div = document.createElement("div");
        div.className = "manip-item";
        div.textContent = "No obvious manipulation signal yet. Keep testing both sides.";
        manipList.appendChild(div);
    }

    // Feedback
    const feedbackBox = document.getElementById("feedback-box");
    if (obs.feedback) {
        feedbackBox.classList.remove("hidden");
        document.getElementById("feedback-text").textContent = obs.feedback;
    } else {
        feedbackBox.classList.add("hidden");
        document.getElementById("feedback-text").textContent = "";
    }

    // Sliders
    buildSliders(obs.evidence_items || []);
    updateActionGuidance();
    updateCoJudgeSummary();
    refreshTourHighlight();
}

function buildSliders(evidenceItems) {
    const container = document.getElementById("slider-container");
    container.innerHTML = "";
    evidenceItems.forEach(ev => {
        const row = document.createElement("div");
        row.className = "slider-row";
        row.innerHTML = `
            <label>${ev.evidence_id}</label>
            <input type="range" min="0" max="1" step="0.05" value="0.5"
                   id="slider-${ev.evidence_id}"
                   oninput="document.getElementById('val-${ev.evidence_id}').textContent=parseFloat(this.value).toFixed(2)">
            <span class="slider-val" id="val-${ev.evidence_id}">0.50</span>
        `;
        container.appendChild(row);
    });
}

// ─── ACTION SELECTION ───────────────────────────────────────
function selectAction(btn) {
    document.querySelectorAll(".action-type-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentAction = btn.dataset.action;

    const verdictSection = document.getElementById("verdict-section");
    if (currentAction === "rule") {
        verdictSection.classList.remove("hidden");
    } else {
        verdictSection.classList.add("hidden");
    }
    updateActionGuidance();
}

// ─── SUBMIT ACTION ──────────────────────────────────────────
async function submitAction() {
    if (isDone || !gameSessionId) return;

    const submitBtn = document.getElementById("btn-submit");
    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Processing...";

    const reasoning = document.getElementById("inp-reasoning").value ||
        "Examining the evidence and testimony to identify inconsistencies and potential fabrication in the presented materials.";

    const action = {
        action_type: currentAction,
        reasoning: reasoning,
        target: document.getElementById("inp-target").value || null,
        evidence_reliability_assessments: {}
    };

    // Collect slider values
    const sliders = document.querySelectorAll('[id^="slider-E"]');
    sliders.forEach(s => {
        const eid = s.id.replace("slider-", "");
        action.evidence_reliability_assessments[eid] = parseFloat(s.value);
    });

    if (currentAction === "rule") {
        action.verdict = document.getElementById("inp-verdict").value;
        action.verdict_reasoning = document.getElementById("inp-verdict-reasoning").value ||
            "Based on thorough examination of all evidence and testimony, the ruling is issued considering credibility assessments and legal precedent.";
    }

    try {
        const res = await fetch(`${BASE}/game/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: gameSessionId, action: action }),
        });
        const data = await res.json();

        const reward = data.reward || 0;
        isDone = data.done || false;
        gameState = data.observation || data;

        // Add log entry
        addLogEntry(gameState.time_step, currentAction, reward);

        // Render updated state
        renderGame();

        // Clear inputs
        document.getElementById("inp-reasoning").value = "";
        document.getElementById("inp-target").value = "";

        // If done, show gavel overlay
        if (isDone) {
            showGavelOverlay(gameState);
        }

    } catch (err) {
        alert("Error communicating with the environment: " + err.message);
        console.error(err);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "⚡ SUBMIT ACTION";
    }
}

// ─── LOG ENTRY ──────────────────────────────────────────────
function addLogEntry(step, action, reward) {
    const container = document.getElementById("log-entries");
    const placeholder = container.querySelector(".log-empty");
    if (placeholder) {
        placeholder.remove();
    }
    const icons = {
        examine_evidence: "🔍",
        question_plaintiff: "❓🔵",
        question_defendant: "❓🔴",
        rule: "⚖️",
    };

    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = `
        <div class="log-step">STEP ${step}</div>
        <div class="log-action">${icons[action] || "📋"} ${action.replace("_", " ")}</div>
        <div class="log-reward">+${reward.toFixed(3)}</div>
    `;
    container.prepend(entry);
}

// ─── GAVEL OVERLAY ──────────────────────────────────────────
function showGavelOverlay(obs) {
    const overlay = document.getElementById("gavel-overlay");
    const scoreDisplay = document.getElementById("final-score-display");
    const score = obs.final_score || obs.cumulative_score || 0;

    let grade, color;
    if (score >= 0.8) { grade = "EXCELLENT"; color = "#2ecc71"; }
    else if (score >= 0.6) { grade = "GOOD"; color = "#f39c12"; }
    else if (score >= 0.4) { grade = "FAIR"; color = "#e67e22"; }
    else { grade = "NEEDS IMPROVEMENT"; color = "#e74c3c"; }

    scoreDisplay.innerHTML = `
        <span style="color:${color}">${score.toFixed(3)}</span>
        <div style="font-size:1rem; color:${color}; margin-top:8px; letter-spacing:3px;">${grade}</div>
    `;

    overlay.classList.remove("hidden");

    // Click to dismiss
    overlay.onclick = () => {
        overlay.classList.add("hidden");
    };
}

document.addEventListener("keydown", (event) => {
    const overlay = document.getElementById("tour-overlay");
    if (!overlay || overlay.classList.contains("hidden")) return;

    if (event.key === "Escape") {
        closeTour();
    } else if (event.key === "ArrowRight") {
        nextTourStep();
    } else if (event.key === "ArrowLeft") {
        prevTourStep();
    }
});
