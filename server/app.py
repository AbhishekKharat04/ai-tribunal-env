"""AI Tribunal Environment — FastAPI App"""
import os, sys, json
from uuid import uuid4
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional

from openenv.core.env_server import create_app
from models import TribunalAction, TribunalObservation
from server.ai_judge import request_hint as request_ai_judge_hint
from server.tribunal_environment import TribunalEnvironment
from server.cases import CASES
from server.case_generator import generate_case as _generate_case


def create_environment() -> TribunalEnvironment:
    level = int(os.environ.get("TASK_LEVEL", "1"))
    return TribunalEnvironment(task_level=level)


app = create_app(
    create_environment,
    TribunalAction,
    TribunalObservation,
    env_name="ai_tribunal_env",
)


# Mount static files (CSS, JS)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    """Serve the game UI if available, otherwise return API info."""
    index_path = os.path.join(static_dir, "index.html") if os.path.exists(static_dir) else None
    if index_path and os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {
        "name": "AI Tribunal Environment",
        "description": "RL environment where agents learn to judge adversarial legal cases with precedent consistency",
        "docs": "/docs",
        "health": "/health",
        "tasks": "/tasks",
        "baseline": "/baseline",
    }


@app.get("/agents.md", response_class=PlainTextResponse)
def agents_md():
    """Agent-friendly entrypoint for tools that discover spaces via plain text."""
    return PlainTextResponse(
        "\n".join(
            [
                "To use this application (ai-tribunal-env: adversarial legal reasoning benchmark):",
                "API schema: GET https://abhishekkharat11-ai-tribunal-env.hf.space/openapi.json",
                "Call endpoint: POST https://abhishekkharat11-ai-tribunal-env.hf.space/game/reset {\"task_level\": 1|2|3} then POST https://abhishekkharat11-ai-tribunal-env.hf.space/game/step {\"session_id\": \"...\", \"action\": {...}}",
                "Poll result: Not required; endpoints return synchronously",
                "Auth: Public Space today. If the Space is made protected/private later, send Bearer $HF_TOKEN",
            ]
        )
    )


# ── Stateful Game Endpoints (for the web UI) ─────────────────
# The game UI keeps its own session-aware environment instances.
_game_envs: Dict[str, TribunalEnvironment] = {}
_ai_judge_calls: Dict[str, int] = {}
AI_JUDGE_MAX_CALLS_PER_SESSION = max(1, int(os.environ.get("AI_JUDGE_MAX_CALLS_PER_SESSION", "3")))


class GameResetRequest(BaseModel):
    task_level: int = 1
    session_id: Optional[str] = None
    continue_session: bool = False


class GameStepRequest(BaseModel):
    session_id: str
    action: Dict


class GameCoJudgeRequest(BaseModel):
    session_id: str


@app.post("/game/reset")
def game_reset(req: GameResetRequest):
    level = max(1, min(len(CASES), req.task_level))
    selected_case = CASES[level - 1]
    session_id = req.session_id or str(uuid4())
    if not req.continue_session:
        TribunalEnvironment.reset_session(session_id)
        _ai_judge_calls.pop(session_id, None)
    game_env = TribunalEnvironment(task_level=selected_case["level"])
    _game_envs[session_id] = game_env
    obs = game_env.reset(
        task_level=selected_case["level"],
        session_id=session_id,
        case_override=selected_case,
    )
    return JSONResponse({
        "session_id": session_id,
        "observation": obs.model_dump(),
        "ai_judge": {
            "max_calls_per_session": AI_JUDGE_MAX_CALLS_PER_SESSION,
            "calls_used": _ai_judge_calls.get(session_id, 0),
            "calls_remaining": max(0, AI_JUDGE_MAX_CALLS_PER_SESSION - _ai_judge_calls.get(session_id, 0)),
        },
    })


class GameGenerateRequest(BaseModel):
    level: Optional[int] = None  # 1=easy, 2=medium, 3=hard. None = random
    domain: Optional[str] = None  # force a specific case_type
    seed: Optional[int] = None  # for reproducibility


@app.post("/game/generate")
def game_generate(req: GameGenerateRequest):
    """Generate a novel procedural case and start a new game session."""
    import random
    seed = req.seed if req.seed is not None else random.randint(0, 999999)
    case = _generate_case(level=req.level, domain=req.domain, seed=seed)
    session_id = str(uuid4())
    TribunalEnvironment.reset_session(session_id)
    game_env = TribunalEnvironment(task_level=case["level"])
    _game_envs[session_id] = game_env
    obs = game_env.reset(
        task_level=case["level"],
        session_id=session_id,
        case_override=case,
    )
    return JSONResponse({
        "session_id": session_id,
        "generated_case": {
            "title": case["title"],
            "case_type": case["case_type"],
            "level": case["level"],
            "max_steps": case["max_steps"],
            "seed": seed,
        },
        "observation": obs.model_dump(),
        "ai_judge": {
            "max_calls_per_session": AI_JUDGE_MAX_CALLS_PER_SESSION,
            "calls_used": 0,
            "calls_remaining": AI_JUDGE_MAX_CALLS_PER_SESSION,
        },
    })


@app.post("/game/step")
def game_step(req: GameStepRequest):
    game_env = _game_envs.get(req.session_id)
    if game_env is None:
        return JSONResponse({"error": "No active game. Call /game/reset first."}, status_code=400)
    try:
        action = TribunalAction(**req.action)
        obs = game_env.step(action)
        reward = float(obs.reward or 0.0)
        done = bool(obs.done)
        info = {
            "step_score": obs.step_score,
            "final_score": obs.final_score,
            "episode_id": obs.metadata.get("episode_id") if obs.metadata else None,
            "session_id": req.session_id,
            "verdict_issued": obs.verdicts_issued > 0,
        }
        return JSONResponse({
            "session_id": req.session_id,
            "observation": obs.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/game/cojudge")
def game_cojudge(req: GameCoJudgeRequest):
    game_env = _game_envs.get(req.session_id)
    if game_env is None:
        return JSONResponse({"error": "No active game. Call /game/reset first."}, status_code=400)

    calls_used = _ai_judge_calls.get(req.session_id, 0)
    calls_remaining = max(0, AI_JUDGE_MAX_CALLS_PER_SESSION - calls_used)
    if calls_remaining <= 0:
        return JSONResponse({
            "enabled": True,
            "session_id": req.session_id,
            "message": f"AI Co-Judge hint budget exhausted for this session ({AI_JUDGE_MAX_CALLS_PER_SESSION} calls).",
            "remaining_hints": 0,
            "suggestion": None,
        })

    result = request_ai_judge_hint(game_env)
    if result.get("enabled"):
        _ai_judge_calls[req.session_id] = calls_used + 1
        calls_used += 1
        calls_remaining = max(0, AI_JUDGE_MAX_CALLS_PER_SESSION - calls_used)

    return JSONResponse({
        "enabled": result.get("enabled", False),
        "session_id": req.session_id,
        "message": result.get("message", ""),
        "model": result.get("model"),
        "remaining_hints": calls_remaining,
        "suggestion": result.get("suggestion"),
    })


@app.get("/tasks")
def get_tasks():
    tasks = []
    for c in CASES:
        tasks.append({
            "task_id": f"task_{c['level']}",
            "name": c["name"],
            "level": c["level"],
            "difficulty": ["easy", "medium", "hard"][c["level"] - 1],
            "max_steps": c["max_steps"],
            "case_title": c["title"],
            "description": c["description"],
        })
    action_schema = {
        "action_type": {"type": "string", "values": ["examine_evidence", "question_plaintiff", "question_defendant", "request_document", "rule", "adjourn"], "required": True},
        "reasoning": {"type": "string", "description": "Agent's explicit reasoning (min 40 words)", "required": True},
        "target": {"type": "string", "description": "Evidence ID or party to target", "required": False},
        "verdict": {"type": "string", "values": ["plaintiff_wins", "defendant_wins", "partial_plaintiff", "partial_defendant", "dismissed"], "required": "when action_type=rule"},
        "verdict_reasoning": {"type": "string", "description": "Full written judgment (min 60 words)", "required": "when action_type=rule"},
        "evidence_reliability_assessments": {"type": "dict[str,float]", "description": "Evidence ID -> reliability score 0-1", "required": False},
    }
    return JSONResponse({"environment": "ai_tribunal_env", "total_tasks": len(tasks), "tasks": tasks, "action_schema": action_schema, "score_range": [0.0, 1.0]})


class GraderRequest(BaseModel):
    action_type: str = "rule"
    reasoning: str = ""
    verdict: Optional[str] = None
    verdict_reasoning: Optional[str] = None
    evidence_reliability_assessments: Dict[str, float] = {}
    task_level: int = 1


@app.post("/grader")
def grade_action(req: GraderRequest):
    from server.grader import grade_step
    case = CASES[req.task_level - 1]
    action = TribunalAction(
        action_type=req.action_type,
        reasoning=req.reasoning,
        verdict=req.verdict,
        verdict_reasoning=req.verdict_reasoning,
        evidence_reliability_assessments=req.evidence_reliability_assessments,
    )
    score, feedback, metrics = grade_step(
        case=case, action=action, step=1,
        history=[], precedent_reward=0.0,
        verdict_issued=(req.verdict is not None),
    )
    return JSONResponse({"task_level": req.task_level, "score": score, "feedback": feedback, "metrics": metrics})


def _run_baseline_task(task_level: int) -> Dict:
    env = TribunalEnvironment(task_level=task_level)
    case = CASES[task_level - 1]
    session_id = f"baseline-{uuid4()}"
    obs = env.reset(task_level=task_level, session_id=session_id)

    BASELINE_ACTIONS = {
        1: [
            TribunalAction(action_type="examine_evidence", reasoning="I will examine all evidence carefully, paying attention to credibility scores and any inconsistencies between items submitted by each party.", target="E3"),
            TribunalAction(action_type="examine_evidence", reasoning="Examining the CCTV claim by defendant. The footage is referenced but not submitted, which raises serious credibility concerns. No footage = unverifiable claim.", target="E4"),
            TribunalAction(action_type="question_defendant", reasoning="The defendant claims CCTV footage exists but has not submitted it. This is a critical gap. I must address why this evidence was withheld from the tribunal."),
            TribunalAction(
                action_type="rule",
                reasoning="Based on examination of all evidence, the plaintiff's case is supported by genuine documentation while defendant's key evidence (E3 inspection report, E4 CCTV claim) is fabricated or unsubstantiated.",
                verdict="plaintiff_wins",
                verdict_reasoning=(
                    "The plaintiff has provided authentic purchase receipt (E1), manufacturer warranty (E5), and contemporaneous complaint messages (E2). "
                    "The defendant's inspection report (E3) lacks a timestamp for when inspection occurred and appears retroactively generated. "
                    "The defendant's CCTV claim (E4) was never substantiated with actual footage — an unsubmitted claim carries no evidentiary weight. "
                    "The Consumer Protection Act 2019 supersedes store policy for manufacturing defects. Plaintiff is awarded full refund of ₹85,000."
                ),
                evidence_reliability_assessments={"E1": 0.95, "E2": 0.90, "E3": 0.20, "E4": 0.10, "E5": 0.95, "E6": 0.75},
            ),
        ],
        2: [
            TribunalAction(action_type="examine_evidence", reasoning="Examining performance log E3 submitted by defendant. The document claims repeated deadline misses but I notice no metadata about when this was created. Suspicious timing relative to HR complaint.", target="E3"),
            TribunalAction(action_type="examine_evidence", reasoning="The plaintiff's promotion letter from 2024 (E7) and performance review from Oct 2025 (E1) directly contradict the sudden performance decline narrative. I must reconcile these.", target="E7"),
            TribunalAction(action_type="question_defendant", reasoning="I need to understand the composition of the 'independent panel' that investigated the HR complaint. The HR head's testimony (E6) claims independence but this requires verification."),
            TribunalAction(action_type="examine_evidence", reasoning="Employment contract clause 8.3 (E5) is clear — PIP is mandatory before termination. The defendant has not contested this clause exists. This is a procedural violation.", target="E5"),
            TribunalAction(
                action_type="rule",
                reasoning="The termination violated the employment contract. Performance documentation was created retroactively. The HR investigation was not independent. Retaliation motive is established by proximity to HR complaint.",
                verdict="plaintiff_wins",
                verdict_reasoning=(
                    "The plaintiff's termination violated Clause 8.3 of her employment contract requiring a Performance Improvement Plan. "
                    "The defendant's performance log (E3) was created in March 2026 — after the HR complaint — showing retroactive documentation. "
                    "The 'independent' investigation panel (E6) was not independent. Two valid performance reviews contradict the sudden decline narrative. "
                    "The 3-week proximity between HR complaint and termination establishes retaliation motive. "
                    "Ruling: Plaintiff is entitled to reinstatement and 18 months compensation."
                ),
                evidence_reliability_assessments={"E1": 0.92, "E2": 0.95, "E3": 0.15, "E4": 0.70, "E5": 0.97, "E6": 0.25, "E7": 0.95},
            ),
        ],
        3: [
            TribunalAction(action_type="examine_evidence", reasoning="Examining the Land Acquisition Notice (E3). The plaintiff claims she never received it. I need to verify postal delivery records and check signature authenticity.", target="E3"),
            TribunalAction(action_type="examine_evidence", reasoning="The compensation payment record (E4) claims money was transferred to plaintiff. Comparing with plaintiff's bank statements (E5) which show no such credit. This is a critical discrepancy.", target="E4"),
            TribunalAction(action_type="examine_evidence", reasoning="RTI response (E7) reveals Mr. Venkat was suspended for corruption in a similar case. This directly impeaches his testimony (E6) about overseeing the acquisition.", target="E7"),
            TribunalAction(action_type="question_defendant", reasoning="The defendant's counsel has made implicit references to political backing and offered ex-gratia payment mid-hearing. I must address this manipulation attempt on record and treat it as evidence of bad faith."),
            TribunalAction(action_type="examine_evidence", reasoning="47 years of property tax receipts (E2) and original 1978 sale deed (E1) establish continuous possession and clear title. The acquisition chain rests entirely on forged documents.", target="E1"),
            TribunalAction(
                action_type="rule",
                reasoning="The entire acquisition chain is built on forged documents. The notice was never served, payment went to a fraudulent account, and the key witness is a known corrupt officer. This is systematic fraud.",
                verdict="plaintiff_wins",
                verdict_reasoning=(
                    "This case involves systematic fraud by the defendant parties. "
                    "The Land Acquisition Notice (E3) was never delivered — postal records and the plaintiff's signature forgery confirm this. "
                    "Compensation (E4) was paid to a fraudulent account — the plaintiff's bank statements (E5) contain no such credit. "
                    "Mr. Venkat's testimony (E6) is inadmissible given his documented history of corruption in similar acquisitions (E7). "
                    "The 47-year continuous possession with tax records (E2) and original registered deed (E1) establish unimpeachable title. "
                    "The ex-gratia offer made mid-hearing constitutes attempted witness influence and is noted as evidence of bad faith. "
                    "Ruling: Sunrise Developers' title is void. Plaintiff's property rights are restored. FIR recommended against Mr. Venkat."
                ),
                evidence_reliability_assessments={"E1": 0.97, "E2": 0.95, "E3": 0.10, "E4": 0.08, "E5": 0.93, "E6": 0.05, "E7": 0.96, "E8": 0.10, "E9": 0.82},
            ),
        ],
    }

    actions = BASELINE_ACTIONS.get(task_level, BASELINE_ACTIONS[1])
    scores = []
    done = False

    for action in actions:
        if done:
            break
        obs = env.step(action)
        reward = float(obs.reward or 0.0)
        done = bool(obs.done)
        scores.append(round(reward, 4))

    TribunalEnvironment.reset_session(session_id)

    final = round(sum(scores) / len(scores), 4) if scores else 0.0
    return {
        "task_level": task_level,
        "task_name": case["name"],
        "case_title": case["title"],
        "steps": len(scores),
        "step_scores": scores,
        "final_score": final,
        "score_range": [0.0, 1.0],
    }


@app.get("/baseline")
def run_baseline(task_level: Optional[int] = None):
    from fastapi import HTTPException
    try:
        if task_level is not None:
            return JSONResponse({"results": [_run_baseline_task(task_level)], "score_range": [0.0, 1.0]})
        results = [_run_baseline_task(lvl) for lvl in [1, 2, 3]]
        overall = round(sum(r["final_score"] for r in results) / 3, 4)
        return JSONResponse({"results": results, "overall_score": overall, "score_range": [0.0, 1.0], "note": "Deterministic baseline"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
