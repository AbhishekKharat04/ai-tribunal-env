/* ═══════════════════════════════════════════════════════════
   AI TRIBUNAL — Game Logic
   Connects to FastAPI backend at /reset, /step
   ═══════════════════════════════════════════════════════════ */

const BASE = window.location.origin;
let currentAction = "examine_evidence";
let gameState = null;
let isDone = false;

// ─── SPLASH → GAME ─────────────────────────────────────────
async function startCase(level) {
    const btn = document.querySelector(`.case-btn[data-level="${level}"]`);
    btn.style.transform = "scale(0.95)";
    btn.style.opacity = "0.7";

    try {
        const res = await fetch(`${BASE}/reset`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_level: level }),
        });
        const data = await res.json();
        gameState = data.observation || data;
        isDone = false;

        renderGame();
        document.getElementById("splash").classList.add("hidden");
        document.getElementById("game").classList.remove("hidden");
    } catch (err) {
        alert("Could not connect to the environment server. Make sure it's running!");
        console.error(err);
    } finally {
        btn.style.transform = "";
        btn.style.opacity = "";
    }
}

function backToSplash() {
    document.getElementById("game").classList.add("hidden");
    document.getElementById("splash").classList.remove("hidden");
    document.getElementById("log-entries").innerHTML = "";
    isDone = false;
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
    manipList.innerHTML = "";
    (obs.manipulative_signals || []).forEach(s => {
        const div = document.createElement("div");
        div.className = "manip-item";
        div.textContent = "⚠️ " + s;
        manipList.appendChild(div);
    });

    // Feedback
    if (obs.feedback) {
        document.getElementById("feedback-box").classList.remove("hidden");
        document.getElementById("feedback-text").textContent = obs.feedback;
    }

    // Sliders
    buildSliders(obs.evidence_items || []);
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
}

// ─── SUBMIT ACTION ──────────────────────────────────────────
async function submitAction() {
    if (isDone) return;

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
        const res = await fetch(`${BASE}/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: action }),
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
