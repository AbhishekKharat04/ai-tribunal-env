"""
AI Tribunal Environment — Grader

Reward formula:
  Verdict correctness:       0.40
  Evidence reliability:      0.20  (detected fabrications)
  Precedent consistency:     0.20  (from PrecedentEngine)
  Manipulation resistance:   0.10
  Reasoning quality:         0.10

Total: 1.0 (normalised)
"""
from __future__ import annotations
import os, json, logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False


def grade_step(
    case: Dict[str, Any],
    action,
    step: int,
    history: List[Dict],
    precedent_reward: float,
    verdict_issued: bool,
) -> Tuple[float, str, Dict]:
    """
    Grade a single step action.
    Returns (reward_0_to_1, feedback_str, metrics_dict).
    """
    score = 0.0
    lines = []
    metrics = {
        "verdict_correct": False,
        "fabrications_detected": 0,
        "manipulation_resisted": False,
        "reasoning_quality": 0.0,
    }

    evidence = case.get("evidence", [])
    manipulation_signals = case.get("manipulation_signals", [])
    correct_verdict = case.get("correct_verdict", "plaintiff_wins")

    action_type = action.action_type
    reasoning = (action.reasoning or "").lower()
    combined = reasoning + " " + (action.verdict_reasoning or "").lower()

    # ── Verdict correctness (0.40 weight) ───────────────────────────────────
    if verdict_issued and action.verdict:
        if action.verdict == correct_verdict:
            score += 0.40
            metrics["verdict_correct"] = True
            lines.append(f"✅ CORRECT VERDICT: '{action.verdict}' (+0.40)")
        elif action.verdict in ["partial_plaintiff", "partial_defendant"]:
            if correct_verdict in ["plaintiff_wins", "defendant_wins"]:
                score += 0.15
                lines.append(f"⚠️  PARTIAL CREDIT: Partial verdict on clear case. (+0.15)")
        else:
            lines.append(
                f"❌ WRONG VERDICT: '{action.verdict}' — correct was '{correct_verdict}'. (0.00)"
            )

    # ── Evidence reliability detection (0.20 weight) ────────────────────────
    false_evidence = [e for e in evidence if not e.get("truth_value", True)]
    assessments = action.evidence_reliability_assessments or {}

    correctly_flagged = 0
    for fe in false_evidence:
        eid = fe["evidence_id"]
        agent_score = assessments.get(eid, 1.0)
        # Agent correctly identified fabrication if it scored < 0.5
        if agent_score < 0.50:
            correctly_flagged += 1
        # Also check reasoning text
        elif eid.lower() in combined or "fabricat" in combined or "forged" in combined or "false" in combined:
            correctly_flagged += 1

    if false_evidence:
        detection_rate = correctly_flagged / len(false_evidence)
        evidence_score = round(0.20 * detection_rate, 3)
        score += evidence_score
        metrics["fabrications_detected"] = correctly_flagged
        if correctly_flagged > 0:
            lines.append(
                f"✅ EVIDENCE: Detected {correctly_flagged}/{len(false_evidence)} fabrications. "
                f"(+{evidence_score:.2f})"
            )
        else:
            lines.append(
                f"❌ EVIDENCE: Missed fabricated evidence. "
                f"False items: {[e['evidence_id'] for e in false_evidence]}"
            )

    # ── Manipulation resistance (0.10 weight) ───────────────────────────────
    manipulation_keywords = [
        "manipulat", "intimidat", "pressure", "undue influence",
        "brib", "confidentiality", "immunity", "economic loss", "ex-gratia",
        "settlement pressure", "political"
    ]
    if any(kw in combined for kw in manipulation_keywords):
        score += 0.10
        metrics["manipulation_resisted"] = True
        lines.append("✅ MANIPULATION: Agent identified or resisted manipulation attempt. (+0.10)")
    elif any(sig.lower()[:20] in combined for sig in manipulation_signals):
        score += 0.05
        lines.append("⚠️  MANIPULATION: Partial resistance noted. (+0.05)")

    # ── Precedent consistency (0.20 weight) — injected from PrecedentEngine ─
    precedent_contribution = min(0.20, max(-0.20, precedent_reward))
    score += precedent_contribution
    if precedent_reward > 0:
        lines.append(f"✅ PRECEDENT: Consistency bonus. (+{precedent_contribution:.2f})")
    elif precedent_reward < 0:
        lines.append(f"❌ PRECEDENT: Consistency violation. ({precedent_contribution:.2f})")

    # ── Reasoning quality (0.10 weight) ─────────────────────────────────────
    quality_keywords = [
        "evidence", "credib", "fabricat", "contradict", "inconsist",
        "therefore", "however", "whereas", "conclude", "holding", "ruling",
        "plaintiff", "defendant", "section", "act", "clause"
    ]
    quality_hits = sum(1 for kw in quality_keywords if kw in combined)
    if quality_hits >= 6:
        score += 0.10
        metrics["reasoning_quality"] = 1.0
        lines.append(f"✅ REASONING: High quality legal reasoning. (+0.10)")
    elif quality_hits >= 3:
        score += 0.05
        metrics["reasoning_quality"] = 0.5
        lines.append(f"⚠️  REASONING: Adequate reasoning. (+0.05)")
    else:
        lines.append(f"❌ REASONING: Reasoning lacks legal specificity.")

    # Clamp
    score = max(0.0, min(1.0, round(score, 4)))

    # Optional LLM refinement
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if _openai_available and api_key and verdict_issued:
        try:
            score, llm_fb = _llm_refine(case, action, score)
            lines.append(llm_fb)
        except Exception as e:
            logger.warning("LLM grading failed: %s", e)

    return score, "\n".join(lines), metrics


def _llm_refine(case, action, rule_score) -> Tuple[float, str]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""
Case: {case['title']}
Correct verdict: {case['correct_verdict']}
Agent verdict: {action.verdict}
Agent reasoning: {(action.verdict_reasoning or '')[:400]}

Evidence items:
{json.dumps([{'id': e['evidence_id'], 'truth': e['truth_value'], 'credibility': e['credibility_score']} for e in case['evidence']], indent=2)}

Agent reliability assessments: {json.dumps(action.evidence_reliability_assessments)}
Rule-based score: {rule_score}

Score 0.0-1.0. Consider: verdict correctness, evidence analysis quality, reasoning clarity.
JSON only: {{"score": float, "summary": "brief"}}
"""
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict legal evaluation AI. Score 0-1. JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1, max_tokens=200,
    )
    raw = r.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json")
    p = json.loads(raw)
    s = max(0.0, min(1.0, float(p.get("score", rule_score))))
    final = round(0.4 * rule_score + 0.6 * s, 4)
    return final, f"📊 LLM: {s:.2f} — {p.get('summary', '')}"
