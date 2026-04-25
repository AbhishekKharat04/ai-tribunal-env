"""
HF Router-backed AI Co-Judge helper.

This lets the CPU-only Space call a large remote model on demand,
using Hugging Face inference credits only when a judge explicitly
asks for assistance.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests


ROUTER_BASE_URL = os.environ.get("HF_ROUTER_BASE_URL", "https://router.huggingface.co/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("AI_JUDGE_MODEL", "Qwen/Qwen2.5-72B-Instruct:fastest")

SYSTEM_PROMPT = """You are an AI co-judge assisting a human judge inside the AI Tribunal benchmark.

Your role is to suggest the NEXT BEST move, not to blindly end the case early.
You must stay grounded in the evidence, manipulation signals, and hearing history.

Return JSON only with this shape:
{
  "recommended_action_type": "examine_evidence|question_plaintiff|question_defendant|rule",
  "target": "E1 or null",
  "recommended_verdict": "plaintiff_wins|defendant_wins|partial_plaintiff|partial_defendant|dismissed or null",
  "why_now": "2-4 sentences explaining why this is the best next move",
  "watch_for": ["short risk or contradiction", "short risk or contradiction"],
  "draft_reasoning": "A concise draft the human judge can adapt into their own reasoning",
  "confidence": 0.0
}

Rules:
- Prefer evidence examination before ruling unless the record is already mature.
- If suggesting a ruling, set recommended_verdict.
- Keep watch_for short and concrete.
- Confidence must be between 0.0 and 1.0.
"""


def _get_token() -> str:
    return os.environ.get("HF_TOKEN") or os.environ.get("API_KEY") or ""


def is_configured() -> bool:
    return bool(_get_token())


def _trim(text: str, limit: int = 320) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _normalize_suggestion(raw: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(fallback)
    if isinstance(raw, dict):
        data.update({k: v for k, v in raw.items() if v is not None})

    action_type = data.get("recommended_action_type") or fallback["recommended_action_type"]
    if action_type not in {"examine_evidence", "question_plaintiff", "question_defendant", "rule"}:
        action_type = fallback["recommended_action_type"]

    verdict = data.get("recommended_verdict")
    if verdict not in {None, "plaintiff_wins", "defendant_wins", "partial_plaintiff", "partial_defendant", "dismissed"}:
        verdict = None

    watch_for = data.get("watch_for")
    if not isinstance(watch_for, list):
        watch_for = fallback["watch_for"]
    watch_for = [_trim(str(item), 120) for item in watch_for[:3]]

    try:
        confidence = float(data.get("confidence", fallback["confidence"]))
    except Exception:
        confidence = fallback["confidence"]
    confidence = max(0.0, min(1.0, confidence))

    return {
        "recommended_action_type": action_type,
        "target": data.get("target"),
        "recommended_verdict": verdict,
        "why_now": _trim(str(data.get("why_now", fallback["why_now"])), 420),
        "watch_for": watch_for,
        "draft_reasoning": _trim(str(data.get("draft_reasoning", fallback["draft_reasoning"])), 520),
        "confidence": confidence,
    }


def _fallback_suggestion(env: Any) -> Dict[str, Any]:
    evidence = env._case.get("evidence", [])
    defendant_items = [item for item in evidence if item.get("submitted_by") == "defendant"]
    suspicious = sorted(defendant_items, key=lambda item: item.get("credibility_score", 1.0))
    target = suspicious[0]["evidence_id"] if suspicious else None
    should_rule = env._step >= max(3, env._case.get("max_steps", 8) - 1)

    return {
        "recommended_action_type": "rule" if should_rule else "examine_evidence",
        "target": None if should_rule else target,
        "recommended_verdict": "plaintiff_wins" if should_rule else None,
        "why_now": (
            "The current record already contains enough contradiction to justify a ruling."
            if should_rule
            else "A defense-side evidence item looks more fragile than the rest of the record, so the next best move is to probe it directly."
        ),
        "watch_for": [
            "Claims that rely on unsubmitted or weakly sourced evidence",
            "Timeline gaps between the story and supporting documents",
        ],
        "draft_reasoning": (
            "I want to stress-test the weakest defense-side evidence before giving it any weight in the final ruling."
            if not should_rule
            else "The documentary record now favors the plaintiff because the defense narrative depends on evidence that remains inconsistent or unsupported."
        ),
        "confidence": 0.55 if not should_rule else 0.62,
    }


def _extract_json_payload(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if "```" in cleaned:
        chunks = [chunk.strip() for chunk in cleaned.split("```") if chunk.strip()]
        if chunks:
            cleaned = chunks[0]
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                return {}
    return {}


def _build_prompt(env: Any) -> str:
    evidence_lines: List[str] = []
    for item in env._case.get("evidence", [])[:10]:
        evidence_lines.append(
            f"- {item.get('evidence_id')} | by={item.get('submitted_by')} | "
            f"cred={item.get('credibility_score', 0.5):.2f} | {item.get('description', '')}"
        )

    recent_history = env._history[-4:]
    precedent_items = env._precedent_engine.get_relevant_precedents(
        env._case.get("case_type", ""),
        env._case.get("key_facts", []),
        exclude_case_id=(env._state.episode_id or "")[:8],
    )

    return (
        f"CASE: {env._case.get('title', '')}\n"
        f"TYPE: {env._case.get('case_type', '')}\n"
        f"TASK LEVEL: {env._task_level}\n"
        f"STEP: {env._step}/{env._case.get('max_steps', '?')}\n"
        f"PLAINTIFF: {_trim(env._case.get('plaintiff', {}).get('statement', ''), 420)}\n"
        f"DEFENDANT: {_trim(env._case.get('defendant', {}).get('statement', ''), 420)}\n"
        f"MANIPULATION SIGNALS: {json.dumps(env._case.get('manipulation_signals', [])[:4])}\n"
        f"RECENT ACTIONS: {json.dumps(recent_history)}\n"
        f"RELEVANT PRECEDENTS: {json.dumps(precedent_items[:3])}\n"
        f"EVIDENCE:\n" + "\n".join(evidence_lines)
    )


def request_hint(env: Any) -> Dict[str, Any]:
    fallback = _fallback_suggestion(env)
    token = _get_token()
    if not token:
        return {
            "enabled": False,
            "model": DEFAULT_MODEL,
            "message": "AI Co-Judge is disabled. Add HF_TOKEN as a Space secret to use Hugging Face inference credits without upgrading the Space to GPU.",
            "suggestion": fallback,
        }

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(env)},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }

    try:
        response = requests.post(
            f"{ROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        suggestion = _normalize_suggestion(_extract_json_payload(content), fallback)
        return {
            "enabled": True,
            "model": DEFAULT_MODEL,
            "message": "AI Co-Judge suggestion generated through the Hugging Face Router.",
            "suggestion": suggestion,
        }
    except Exception as exc:
        return {
            "enabled": True,
            "model": DEFAULT_MODEL,
            "message": f"AI Co-Judge fell back to a local heuristic because the remote call failed: {str(exc)[:180]}",
            "suggestion": fallback,
        }
