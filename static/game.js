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
let selectedEvidenceId = null;
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

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function getCredibilityTone(score) {
    if (score >= 0.85) {
        return { color: "#2ecc71", label: "High confidence" };
    }
    if (score >= 0.65) {
        return { color: "#f39c12", label: "Mixed confidence" };
    }
    return { color: "#e74c3c", label: "Fragile record" };
}

function inferEvidenceTestingNote(ev) {
    const score = ev?.credibility_score ?? 0.5;
    const description = (ev?.description || "").toLowerCase();

    if (score < 0.65 && ev?.submitted_by === "defendant") {
        return "This is a defense-side record with weak visible credibility. It is a strong challenge candidate before you trust the defense narrative.";
    }
    if (description.includes("log") || description.includes("report") || description.includes("memo") || description.includes("policy")) {
        return "Internal records can sound official while hiding missing metadata. Cross-check authorship, timing, and whether the source can be independently verified.";
    }
    if (score >= 0.85) {
        return "High visible credibility does not end the inquiry. Treat this as strong surface evidence, then test whether the underlying provenance actually holds up.";
    }
    return "This item deserves comparison against the opposing side's timeline, because medium-confidence evidence often becomes decisive only after contradiction testing.";
}

function selectEvidence(evidenceId) {
    selectedEvidenceId = evidenceId;
    document.getElementById("inp-target").value = evidenceId;
    document.querySelectorAll(".evidence-card").forEach((card) => {
        card.classList.toggle("selected", card.dataset.evidenceId === evidenceId);
    });
    if (gameState) {
        renderBenchInsights(gameState);
    }
}

function renderBenchInsights(obs) {
    const evidenceItems = obs.evidence_items || [];
    const plaintiffItems = evidenceItems.filter((ev) => ev.submitted_by === "plaintiff");
    const defendantItems = evidenceItems.filter((ev) => ev.submitted_by === "defendant");
    const avgCredibility = evidenceItems.length
        ? evidenceItems.reduce((sum, ev) => sum + (ev.credibility_score || 0), 0) / evidenceItems.length
        : 0;
    const stepsUsed = obs.time_step || 0;
    const maxSteps = Math.max(obs.max_steps || 1, 1);
    const stepsRemaining = Math.max(maxSteps - stepsUsed, 0);
    const progressPercent = Math.min(100, Math.round((stepsUsed / maxSteps) * 100));
    const generatedCase = (obs.task_name || "").startsWith("Generated_");

    if (selectedEvidenceId && !evidenceItems.some((ev) => ev.evidence_id === selectedEvidenceId)) {
        selectedEvidenceId = null;
    }
    if (!selectedEvidenceId && evidenceItems.length) {
        selectedEvidenceId = evidenceItems[0].evidence_id;
    }

    const suspiciousItems = [...evidenceItems]
        .sort((a, b) => (a.credibility_score || 0) - (b.credibility_score || 0))
        .slice(0, 2)
        .map((ev) => ev.evidence_id);

    const snapshotMetrics = document.getElementById("snapshot-metrics");
    snapshotMetrics.innerHTML = `
        <div class="metric-tile">
            <span class="metric-label">Evidence Board</span>
            <span class="metric-value">${evidenceItems.length}</span>
            <span class="metric-subvalue">${plaintiffItems.length} plaintiff · ${defendantItems.length} defense</span>
        </div>
        <div class="metric-tile">
            <span class="metric-label">Visible Credibility</span>
            <span class="metric-value">${Math.round(avgCredibility * 100)}%</span>
            <span class="metric-subvalue">Average surface confidence across the board</span>
        </div>
        <div class="metric-tile">
            <span class="metric-label">Step Budget</span>
            <span class="metric-value">${stepsRemaining}</span>
            <span class="metric-subvalue">${stepsUsed} used · ${maxSteps} total</span>
        </div>
        <div class="metric-tile">
            <span class="metric-label">Pressure Signals</span>
            <span class="metric-value">${(obs.manipulative_signals || []).length}</span>
            <span class="metric-subvalue">${suspiciousItems.length ? `Weakest: ${suspiciousItems.join(", ")}` : "No weak record yet"}</span>
        </div>
    `;

    document.getElementById("hearing-progress-fill").style.width = `${progressPercent}%`;
    document.getElementById("hearing-progress-copy").textContent =
        progressPercent < 35
            ? `Early hearing stage. Use these turns to probe the weakest records before committing to a final theory.`
            : progressPercent < 75
                ? `Mid-hearing. Start turning contradictions into a concrete ruling theory while you still have ${stepsRemaining} move${stepsRemaining === 1 ? "" : "s"} left.`
                : `Late hearing. You have ${stepsRemaining} move${stepsRemaining === 1 ? "" : "s"} left, so every action should tighten the final judgment.`;
    document.getElementById("insight-step-copy").textContent = generatedCase
        ? "Generated hearing: fresh case structure, same judging mechanics."
        : "Curated hearing: benchmark case with fixed adversarial traps.";

    document.getElementById("brief-badge").textContent = generatedCase
        ? "Generated case"
        : `Task ${obs.task_level}`;
    document.getElementById("case-brief").textContent =
        obs.task_description || obs.feedback || "Use the evidence board to build a defensible ruling theory.";

    const caseFlags = document.getElementById("case-flags");
    caseFlags.innerHTML = "";
    [
        `${(obs.case_type || "case").replaceAll("_", " ")}`,
        `${obs.max_steps || "?"} total steps`,
        `${(obs.manipulative_signals || []).length} manipulation flags`,
        `${(obs.consistency_score || 1).toFixed(2)} consistency`,
    ].forEach((flag) => {
        const chip = document.createElement("span");
        chip.className = "case-flag";
        chip.textContent = flag;
        caseFlags.appendChild(chip);
    });

    const credibilityMap = document.getElementById("credibility-map");
    credibilityMap.innerHTML = "";
    evidenceItems.forEach((ev) => {
        const tone = getCredibilityTone(ev.credibility_score || 0);
        const row = document.createElement("div");
        row.className = `credibility-row${selectedEvidenceId === ev.evidence_id ? " selected" : ""}`;
        row.onclick = () => selectEvidence(ev.evidence_id);
        row.innerHTML = `
            <div class="credibility-row-head">
                <span class="credibility-row-id">${escapeHtml(ev.evidence_id)}</span>
                <span class="credibility-row-score">${Math.round((ev.credibility_score || 0) * 100)}%</span>
            </div>
            <div class="credibility-row-meta">${escapeHtml(ev.submitted_by === "plaintiff" ? "Plaintiff-submitted" : "Defense-submitted")} · ${escapeHtml(tone.label)}</div>
            <div class="credibility-row-bar">
                <span class="credibility-row-fill" style="width:${(ev.credibility_score || 0) * 100}%; background:${tone.color};"></span>
            </div>
        `;
        credibilityMap.appendChild(row);
    });

    const selectedEvidence = evidenceItems.find((ev) => ev.evidence_id === selectedEvidenceId);
    const selectedEvidenceLabel = document.getElementById("selected-evidence-label");
    const selectedEvidenceCard = document.getElementById("selected-evidence-card");
    if (!selectedEvidence) {
        selectedEvidenceLabel.textContent = "Click any card to inspect it in full";
        selectedEvidenceCard.innerHTML = `<div class="selected-evidence-empty">Evidence notes will appear here once a card is selected.</div>`;
        return;
    }

    const selectedTone = getCredibilityTone(selectedEvidence.credibility_score || 0);
    selectedEvidenceLabel.textContent = `${selectedEvidence.evidence_id} · ${selectedTone.label}`;
    selectedEvidenceCard.innerHTML = `
        <div class="selected-evidence-top">
            <div>
                <div class="selected-evidence-party">${escapeHtml(selectedEvidence.submitted_by === "plaintiff" ? "Plaintiff-submitted" : "Defense-submitted")}</div>
                <div class="selected-evidence-title">${escapeHtml(selectedEvidence.evidence_id)} · ${escapeHtml(selectedEvidence.evidence_type || "evidence")}</div>
            </div>
            <span class="case-flag">${Math.round((selectedEvidence.credibility_score || 0) * 100)}% visible credibility</span>
        </div>
        <p class="selected-evidence-description">${escapeHtml(selectedEvidence.description || "")}</p>
        <div class="selected-evidence-notes">
            <div class="selected-note">
                <span class="selected-note-label">Why it matters</span>
                <span class="selected-note-value">${escapeHtml(inferEvidenceTestingNote(selectedEvidence))}</span>
            </div>
            <div class="selected-note">
                <span class="selected-note-label">Best courtroom move</span>
                <span class="selected-note-value">${selectedTone.label === "Fragile record"
                    ? "Challenge this record directly or question the side that submitted it."
                    : "Cross-check this against an opposing document before you give it decisive weight."}</span>
            </div>
        </div>
    `;
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
    selectedEvidenceId = null;
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
    const evidenceItems = obs.evidence_items || [];
    if (selectedEvidenceId && !evidenceItems.some((ev) => ev.evidence_id === selectedEvidenceId)) {
        selectedEvidenceId = null;
    }
    if (!selectedEvidenceId && evidenceItems.length) {
        selectedEvidenceId = evidenceItems[0].evidence_id;
    }

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
    evidenceItems.forEach(ev => {
        const cred = ev.credibility_score || 0.5;
        let credColor;
        if (cred >= 0.8) credColor = "#2ecc71";
        else if (cred >= 0.5) credColor = "#f39c12";
        else credColor = "#e74c3c";

        const card = document.createElement("div");
        card.className = "evidence-card";
        card.dataset.evidenceId = ev.evidence_id;
        if (selectedEvidenceId === ev.evidence_id) {
            card.classList.add("selected");
        }
        card.onclick = () => {
            selectEvidence(ev.evidence_id);
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

    renderBenchInsights(obs);

    // Sliders
    buildSliders(evidenceItems);
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
