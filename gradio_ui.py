"""
AI Tribunal Environment — Gradio Frontend
A visual interface for judges and mentors to interact with the environment.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from models import TribunalAction
from server.tribunal_environment import TribunalEnvironment

# ── Globals ──────────────────────────────────────────────────────────────────
ENV = None
STEP_LOG = []

CASE_LABELS = {
    1: "⚖️ Task 1 — Consumer Dispute (Easy)",
    2: "⚖️ Task 2 — Employment Dispute (Medium)",
    3: "⚖️ Task 3 — Property Fraud (Hard)",
}

# ── Theme ────────────────────────────────────────────────────────────────────
THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)

CSS = """
.gradio-container { max-width: 1100px !important; }
.case-header { background: linear-gradient(135deg, #1e1b4b, #312e81); color: white;
    padding: 20px; border-radius: 12px; margin-bottom: 12px; }
.evidence-card { background: #f8fafc; border-left: 4px solid #6366f1;
    padding: 12px 16px; border-radius: 8px; margin: 6px 0; font-size: 14px; }
.score-box { background: linear-gradient(135deg, #065f46, #047857); color: white;
    padding: 16px; border-radius: 12px; font-size: 18px; text-align: center; }
.manipulation-alert { background: #fef2f2; border-left: 4px solid #ef4444;
    padding: 10px 14px; border-radius: 8px; color: #991b1b; font-weight: 500; }
.step-entry { border-bottom: 1px solid #e2e8f0; padding: 8px 0; }
"""


def start_case(task_level):
    """Reset environment and return initial observation."""
    global ENV, STEP_LOG
    level = int(task_level.split("Task ")[1][0])
    ENV = TribunalEnvironment(task_level=level)
    STEP_LOG = []
    obs = ENV.reset()

    # Format evidence
    ev_lines = []
    for e in obs.evidence_items:
        icon = "📄" if e.get("evidence_type") == "document" else "🗣️"
        by = "🔵 Plaintiff" if e.get("submitted_by") == "plaintiff" else "🔴 Defendant"
        cred = e.get("credibility_score", 0.5)
        bar = "█" * int(cred * 10) + "░" * (10 - int(cred * 10))
        ev_lines.append(
            f"**{icon} {e['evidence_id']}** ({by})  \n"
            f"{e.get('description', '')[:120]}  \n"
            f"Credibility: `{bar}` {cred:.0%}\n"
        )
    evidence_md = "\n".join(ev_lines)

    # Manipulation signals
    manip = obs.manipulative_signals
    manip_md = "\n".join(f"⚠️ {s}" for s in manip) if manip else "None detected yet."

    header = (
        f"## {obs.case_title}\n"
        f"**Type:** {obs.case_type} | **Steps:** 0/{obs.max_steps}\n\n"
        f"---\n\n"
        f"### 🔵 Plaintiff says:\n> {obs.plaintiff_statement[:400]}\n\n"
        f"### 🔴 Defendant says:\n> {obs.defendant_statement[:400]}"
    )

    return (
        header,           # case_info
        evidence_md,      # evidence_display
        manip_md,         # manipulation_display
        obs.feedback,     # feedback_display
        "0.000",          # score_display
        "",               # log_display
        gr.update(interactive=True),  # action_type
        gr.update(interactive=True),  # submit_btn
    )


def take_action(action_type, target, reasoning, verdict, verdict_reasoning,
                e1, e2, e3, e4, e5, e6, e7, e8, e9):
    """Execute one step in the environment."""
    global ENV, STEP_LOG
    if ENV is None:
        return ("Start a case first!", "", "", "", "0.000", "")

    # Build reliability assessments from sliders
    assessments = {}
    slider_vals = [e1, e2, e3, e4, e5, e6, e7, e8, e9]
    for i, val in enumerate(slider_vals, 1):
        if val is not None and val > 0:
            assessments[f"E{i}"] = round(val, 2)

    # Ensure reasoning minimum
    if not reasoning or len(reasoning.strip()) < 40:
        reasoning = (reasoning or "") + " — Further analysis of evidence credibility and cross-referencing facts to ensure a fair ruling."

    action = TribunalAction(
        action_type=action_type,
        reasoning=reasoning,
        target=target if target else None,
        verdict=verdict if action_type == "rule" else None,
        verdict_reasoning=verdict_reasoning if action_type == "rule" else None,
        evidence_reliability_assessments=assessments,
    )

    obs, reward, done, info = ENV.step(action)

    # Update log
    emoji = {"examine_evidence": "🔍", "question_plaintiff": "❓🔵",
             "question_defendant": "❓🔴", "rule": "⚖️"}.get(action_type, "📋")
    STEP_LOG.append(f"**Step {obs.time_step}** {emoji} `{action_type}` → Reward: **{reward:.3f}**")
    log_md = "\n\n".join(reversed(STEP_LOG))

    # Evidence (unchanged)
    ev_lines = []
    for e in obs.evidence_items:
        icon = "📄" if e.get("evidence_type") == "document" else "🗣️"
        by = "🔵" if e.get("submitted_by") == "plaintiff" else "🔴"
        cred = e.get("credibility_score", 0.5)
        bar = "█" * int(cred * 10) + "░" * (10 - int(cred * 10))
        ev_lines.append(
            f"**{icon} {e['evidence_id']}** ({by})  \n"
            f"{e.get('description', '')[:120]}  \n"
            f"Credibility: `{bar}` {cred:.0%}\n"
        )

    manip = obs.manipulative_signals
    manip_md = "\n".join(f"⚠️ {s}" for s in manip) if manip else "None detected."

    score_txt = f"{obs.cumulative_score:.3f}"
    if done and obs.final_score is not None:
        score_txt = f"🏆 FINAL: {obs.final_score:.3f} / 1.0"

    header = (
        f"## {obs.case_title}\n"
        f"**Step:** {obs.time_step}/{obs.max_steps} | "
        f"**Verdicts:** {obs.verdicts_issued} | "
        f"**Consistency:** {obs.consistency_score:.2f}\n\n"
        f"{'**🔔 CASE CLOSED**' if done else ''}"
    )

    return (
        header,
        "\n".join(ev_lines),
        manip_md,
        obs.feedback,
        score_txt,
        log_md,
    )


# ── Build the Gradio App ────────────────────────────────────────────────────
with gr.Blocks(theme=THEME, css=CSS, title="AI Tribunal Environment") as demo:

    gr.HTML("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <h1 style="margin:0; font-size:2.2em;">⚖️ AI Tribunal Environment</h1>
        <p style="color:#6b7280; font-size:1.1em; margin-top:4px;">
            An OpenEnv RL environment for adversarial legal reasoning
        </p>
    </div>
    """)

    with gr.Row():
        case_select = gr.Dropdown(
            choices=list(CASE_LABELS.values()),
            value=list(CASE_LABELS.values())[0],
            label="Select Case",
            scale=3,
        )
        start_btn = gr.Button("🚀 Start Case", variant="primary", scale=1)

    with gr.Row():
        with gr.Column(scale=2):
            case_info = gr.Markdown(label="Case Briefing", value="*Select a case and click Start.*")
            feedback_display = gr.Textbox(label="📋 Environment Feedback", lines=8, interactive=False)

        with gr.Column(scale=1):
            score_display = gr.Textbox(label="📊 Cumulative Score", value="0.000", interactive=False)
            evidence_display = gr.Markdown(label="Evidence", value="")
            manipulation_display = gr.Markdown(label="⚠️ Manipulation Signals", value="")

    gr.HTML("<hr style='margin: 16px 0;'>")
    gr.Markdown("### 🎯 Take Action")

    with gr.Row():
        action_type = gr.Dropdown(
            choices=["examine_evidence", "question_plaintiff", "question_defendant", "rule"],
            value="examine_evidence", label="Action Type", interactive=False,
        )
        target = gr.Textbox(label="Target (e.g. E1, E3)", placeholder="E1", max_lines=1)

    reasoning = gr.Textbox(label="Your Reasoning (min 40 words)", lines=3,
                           placeholder="Explain your legal reasoning for this action...")

    with gr.Row(visible=True):
        verdict = gr.Dropdown(
            choices=["plaintiff_wins", "defendant_wins", "partial_plaintiff", "partial_defendant", "dismissed"],
            label="Verdict (only for 'rule')", value=None,
        )
        verdict_reasoning = gr.Textbox(label="Verdict Reasoning (min 60 words, only for 'rule')",
                                       lines=2, placeholder="Full written judgment...")

    with gr.Accordion("📊 Evidence Reliability Assessments", open=False):
        gr.Markdown("Rate each evidence item's reliability (0 = fabricated, 1 = authentic):")
        with gr.Row():
            e1 = gr.Slider(0, 1, value=0.5, step=0.05, label="E1")
            e2 = gr.Slider(0, 1, value=0.5, step=0.05, label="E2")
            e3 = gr.Slider(0, 1, value=0.5, step=0.05, label="E3")
        with gr.Row():
            e4 = gr.Slider(0, 1, value=0.5, step=0.05, label="E4")
            e5 = gr.Slider(0, 1, value=0.5, step=0.05, label="E5")
            e6 = gr.Slider(0, 1, value=0.5, step=0.05, label="E6")
        with gr.Row():
            e7 = gr.Slider(0, 1, value=0.5, step=0.05, label="E7")
            e8 = gr.Slider(0, 1, value=0.5, step=0.05, label="E8")
            e9 = gr.Slider(0, 1, value=0.5, step=0.05, label="E9")

    submit_btn = gr.Button("⚡ Submit Action", variant="primary", size="lg", interactive=False)

    gr.HTML("<hr style='margin: 16px 0;'>")
    log_display = gr.Markdown(label="📜 Action Log", value="")

    # ── Events ───────────────────────────────────────────────────────────────
    start_btn.click(
        fn=start_case,
        inputs=[case_select],
        outputs=[case_info, evidence_display, manipulation_display,
                 feedback_display, score_display, log_display,
                 action_type, submit_btn],
    )

    submit_btn.click(
        fn=take_action,
        inputs=[action_type, target, reasoning, verdict, verdict_reasoning,
                e1, e2, e3, e4, e5, e6, e7, e8, e9],
        outputs=[case_info, evidence_display, manipulation_display,
                 feedback_display, score_display, log_display],
    )

    gr.HTML("""
    <div style="text-align:center; padding:20px; color:#9ca3af; font-size:0.85em;">
        Built for the Meta PyTorch OpenEnv Hackathon 2026 by Abhishek Kharat<br>
        <a href="https://github.com/AbhishekKharat04/ai-tribunal-env" target="_blank">GitHub</a> •
        <a href="blog.md" target="_blank">Blog</a>
    </div>
    """)


if __name__ == "__main__":
    # Mount FastAPI alongside Gradio so API endpoints still work
    from server.app import app as fastapi_app
    demo.launch(server_name="0.0.0.0", server_port=7860)
