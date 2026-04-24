"""
AI Tribunal Environment — Core Environment
"""
from __future__ import annotations
import copy, sys, os
from uuid import uuid4
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from models import TribunalAction, TribunalObservation
from server.cases import CASES
from server.grader import grade_step
from server.precedent_engine import PrecedentEngine


class TribunalEnvironment(Environment):
    """
    AI Tribunal Environment.
    Agent acts as judge across 3 adversarial cases.
    Key mechanic: Precedent Consistency Engine penalises
    agents that rule inconsistently on similar cases.
    """

    def __init__(self, task_level: int = 1):
        self._task_level = max(1, min(3, task_level))
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._case: Dict[str, Any] = {}
        self._step = 0
        self._done = False
        self._cumulative_score = 0.0
        self._history: List[Dict] = []
        self._verdicts_issued = 0
        self._manipulation_resisted = 0
        self._precedent_engine = PrecedentEngine()

    def reset(self, task_level: Optional[int] = None) -> TribunalObservation:
        if task_level is not None:
            self._task_level = max(1, min(3, task_level))

        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._step = 0
        self._done = False
        self._cumulative_score = 0.0
        self._history = []
        self._verdicts_issued = 0
        self._manipulation_resisted = 0
        self._precedent_engine.reset()

        self._case = CASES[self._task_level - 1]

        evidence_for_obs = [
            {k: v for k, v in e.items() if k != "truth_value" and k != "notes"}
            for e in self._case["evidence"]
        ]

        return TribunalObservation(
            case_id=self._state.episode_id[:8],
            case_title=self._case["title"],
            case_type=self._case["case_type"],
            task_level=self._task_level,
            task_name=self._case["name"],
            plaintiff_statement=self._case["plaintiff"]["statement"],
            defendant_statement=self._case["defendant"]["statement"],
            plaintiff_profile=self._case["plaintiff"]["profile"],
            defendant_profile=self._case["defendant"]["profile"],
            evidence_items=evidence_for_obs,
            manipulative_signals=self._case["manipulation_signals"],
            relevant_precedents=[],
            time_step=0,
            max_steps=self._case["max_steps"],
            done=False,
            reward=0.0,
            step_score=0.0,
            cumulative_score=0.0,
            final_score=None,
            feedback=(
                f"Case opened: {self._case['title']}\n\n"
                f"{self._case['description']}\n\n"
                f"You have {self._case['max_steps']} steps to examine evidence "
                f"and issue a ruling. Available actions: examine_evidence, "
                f"question_plaintiff, question_defendant, request_document, rule, adjourn."
            ),
            verdicts_issued=0,
            consistency_score=1.0,
            manipulation_resisted=0,
            task_description=self._case["description"],
        )

    def step(self, action: TribunalAction) -> Tuple[TribunalObservation, float, bool, Dict]:
        if self._done:
            raise RuntimeError("Episode done. Call reset().")

        self._state.step_count += 1
        self._step += 1

        verdict_issued = (
            action.action_type == "rule" and action.verdict is not None
        )

        # Get precedent reward if verdict issued
        precedent_reward = 0.0
        precedent_fb = ""
        if verdict_issued:
            precedent_reward, precedent_fb = self._precedent_engine.add_verdict(
                case_id=self._state.episode_id[:8],
                case_type=self._case["case_type"],
                key_facts=self._case["key_facts"],
                verdict=action.verdict,
                step=self._step,
                task_level=self._task_level,
            )
            self._verdicts_issued += 1

        # Grade
        step_score, feedback, metrics = grade_step(
            case=self._case,
            action=action,
            step=self._step,
            history=self._history,
            precedent_reward=precedent_reward,
            verdict_issued=verdict_issued,
        )

        if precedent_fb:
            feedback = precedent_fb + "\n\n" + feedback

        if metrics.get("manipulation_resisted"):
            self._manipulation_resisted += 1

        self._cumulative_score += step_score
        self._history.append({
            "step": self._step,
            "action_type": action.action_type,
            "verdict": action.verdict,
            "score": step_score,
        })

        # Episode ends when verdict issued OR max steps reached
        self._done = verdict_issued or self._step >= self._case["max_steps"]

        final_score = None
        if self._done:
            steps_used = max(1, self._step)
            final_score = round(self._cumulative_score / steps_used, 4)
            consistency = self._precedent_engine.get_consistency_score()
            feedback += (
                f"\n\n{'='*50}\n"
                f"CASE CLOSED\n"
                f"Final Score:         {final_score:.4f} / 1.0\n"
                f"Consistency Score:   {consistency:.3f}\n"
                f"Fabrications Found:  {metrics.get('fabrications_detected', 0)}\n"
                f"Manipulation Blocks: {self._manipulation_resisted}\n"
                f"{'='*50}"
            )

        # Get precedents for next obs
        precedents = self._precedent_engine.get_relevant_precedents(
            self._case["case_type"],
            self._case["key_facts"],
            exclude_case_id=self._state.episode_id[:8],
        )

        evidence_for_obs = [
            {k: v for k, v in e.items() if k != "truth_value" and k != "notes"}
            for e in self._case["evidence"]
        ]

        obs = TribunalObservation(
            case_id=self._state.episode_id[:8],
            case_title=self._case["title"],
            case_type=self._case["case_type"],
            task_level=self._task_level,
            task_name=self._case["name"],
            plaintiff_statement=self._case["plaintiff"]["statement"],
            defendant_statement=self._case["defendant"]["statement"],
            plaintiff_profile=self._case["plaintiff"]["profile"],
            defendant_profile=self._case["defendant"]["profile"],
            evidence_items=evidence_for_obs,
            manipulative_signals=self._case["manipulation_signals"],
            relevant_precedents=precedents,
            time_step=self._step,
            max_steps=self._case["max_steps"],
            done=self._done,
            reward=step_score,
            step_score=step_score,
            cumulative_score=self._cumulative_score,
            final_score=final_score,
            feedback=feedback,
            verdicts_issued=self._verdicts_issued,
            consistency_score=self._precedent_engine.get_consistency_score(),
            manipulation_resisted=self._manipulation_resisted,
            task_description=self._case["description"],
        )

        info = {
            "step_score": step_score,
            "final_score": final_score,
            "verdict_issued": verdict_issued,
            "episode_id": self._state.episode_id,
        }

        return obs, step_score, self._done, info

    @property
    def state(self) -> State:
        return self._state
