"""
AI Tribunal Environment — Core Environment
"""
from __future__ import annotations
import copy, sys, os
from threading import RLock
from uuid import uuid4
from typing import Any, Dict, List, Optional

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

    Precedent state is scoped to a logical session so that
    rulings from earlier cases influence later ones in the same run
    without leaking across unrelated users or benchmarks.
    """

    # Process-local stores used to reconstruct state for stateless HTTP requests.
    _store_lock = RLock()
    _session_precedents: Dict[str, PrecedentEngine] = {}
    _episode_snapshots: Dict[str, Dict[str, Any]] = {}

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
        self._session_id = ""
        self._precedent_engine = PrecedentEngine()

    @classmethod
    def _get_precedent_engine(cls, session_id: str) -> PrecedentEngine:
        with cls._store_lock:
            engine = cls._session_precedents.get(session_id)
            if engine is None:
                engine = PrecedentEngine()
                cls._session_precedents[session_id] = engine
            return engine

    @classmethod
    def _get_snapshot(cls, episode_id: str) -> Optional[Dict[str, Any]]:
        with cls._store_lock:
            snapshot = cls._episode_snapshots.get(episode_id)
            return copy.deepcopy(snapshot) if snapshot is not None else None

    @classmethod
    def _put_snapshot(cls, episode_id: str, snapshot: Dict[str, Any]) -> None:
        with cls._store_lock:
            cls._episode_snapshots[episode_id] = copy.deepcopy(snapshot)

    @classmethod
    def _drop_snapshot(cls, episode_id: str) -> None:
        with cls._store_lock:
            cls._episode_snapshots.pop(episode_id, None)

    @classmethod
    def reset_session(cls, session_id: str) -> None:
        with cls._store_lock:
            cls._session_precedents.pop(session_id, None)
            to_delete = [
                episode_id
                for episode_id, snapshot in cls._episode_snapshots.items()
                if snapshot.get("session_id") == session_id
            ]
            for episode_id in to_delete:
                cls._episode_snapshots.pop(episode_id, None)

    def _persist_snapshot(self) -> None:
        episode_id = self._state.episode_id or ""
        if not episode_id:
            return
        snapshot = {
            "session_id": self._session_id,
            "task_level": self._task_level,
            "step": self._step,
            "done": self._done,
            "cumulative_score": self._cumulative_score,
            "history": copy.deepcopy(self._history),
            "verdicts_issued": self._verdicts_issued,
            "manipulation_resisted": self._manipulation_resisted,
            "step_count": self._state.step_count,
            "case": copy.deepcopy(self._case),
        }
        self._put_snapshot(episode_id, snapshot)

    def _hydrate_from_snapshot(
        self,
        episode_id: Optional[str],
        session_id: Optional[str],
        task_level: Optional[int],
    ) -> bool:
        if not episode_id:
            return False

        snapshot = self._get_snapshot(episode_id)
        if snapshot is None:
            return False

        self._session_id = session_id or snapshot["session_id"]
        self._task_level = max(1, min(3, int(task_level or snapshot["task_level"])))
        self._precedent_engine = self._get_precedent_engine(self._session_id)
        self._state = State(
            episode_id=episode_id,
            step_count=int(snapshot["step_count"]),
        )
        self._step = int(snapshot["step"])
        self._done = bool(snapshot["done"])
        self._cumulative_score = float(snapshot["cumulative_score"])
        self._history = copy.deepcopy(snapshot["history"])
        self._verdicts_issued = int(snapshot["verdicts_issued"])
        self._manipulation_resisted = int(snapshot["manipulation_resisted"])
        snapshot_case = snapshot.get("case")
        if snapshot_case:
            self._case = copy.deepcopy(snapshot_case)
            self._task_level = max(
                1,
                min(3, int(self._case.get("level", self._task_level))),
            )
        else:
            self._case = CASES[self._task_level - 1]
        return True

    def _build_observation(
        self,
        reward: float,
        step_score: float,
        final_score: Optional[float],
        feedback: str,
        precedents: List[Dict[str, Any]],
    ) -> TribunalObservation:
        evidence_for_obs = [
            {k: v for k, v in e.items() if k != "truth_value" and k != "notes"}
            for e in self._case["evidence"]
        ]
        return TribunalObservation(
            case_id=(self._state.episode_id or "")[:8],
            episode_id=self._state.episode_id or "",
            session_id=self._session_id,
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
            reward=reward,
            step_score=step_score,
            cumulative_score=self._cumulative_score,
            final_score=final_score,
            feedback=feedback,
            verdicts_issued=self._verdicts_issued,
            consistency_score=self._precedent_engine.get_consistency_score(),
            manipulation_resisted=self._manipulation_resisted,
            task_description=self._case["description"],
            metadata={
                "session_id": self._session_id,
                "episode_id": self._state.episode_id,
            },
        )

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_level: Optional[int] = None,
        session_id: Optional[str] = None,
        case_override: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> TribunalObservation:
        selected_case = case_override or kwargs.get("case_override")

        if task_level is not None:
            self._task_level = max(1, min(3, task_level))
        elif kwargs.get("task_level") is not None:
            self._task_level = max(1, min(3, int(kwargs["task_level"])))

        self._session_id = (
            session_id
            or kwargs.get("session_id")
            or str(uuid4())
        )
        self._precedent_engine = self._get_precedent_engine(self._session_id)
        resolved_episode_id = episode_id or kwargs.get("episode_id") or str(uuid4())
        self._state = State(episode_id=resolved_episode_id, step_count=0)
        self._step = 0
        self._done = False
        self._cumulative_score = 0.0
        self._history = []
        self._verdicts_issued = 0
        self._manipulation_resisted = 0

        if selected_case is not None:
            self._case = copy.deepcopy(selected_case)
            self._task_level = max(
                1,
                min(3, int(self._case.get("level", self._task_level))),
            )
        else:
            self._case = CASES[self._task_level - 1]
        self._persist_snapshot()
        return self._build_observation(
            reward=0.0,
            step_score=0.0,
            final_score=None,
            feedback=(
                f"Case opened: {self._case['title']}\n\n"
                f"{self._case['description']}\n\n"
                f"You have {self._case['max_steps']} steps to examine evidence "
                f"and issue a ruling. Available actions: examine_evidence, "
                f"question_plaintiff, question_defendant, request_document, rule, adjourn."
            ),
            precedents=[],
        )

    def step(
        self,
        action: TribunalAction,
        timeout_s: Optional[float] = None,
        episode_id: Optional[str] = None,
        task_level: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> TribunalObservation:
        meta = action.metadata or {}
        resolved_episode_id = episode_id or kwargs.get("episode_id") or meta.get("episode_id")
        resolved_session_id = session_id or kwargs.get("session_id") or meta.get("session_id")
        resolved_task_level = task_level or kwargs.get("task_level")

        # Auto-hydrate if step() is called on a fresh instance via stateless HTTP.
        if not self._case:
            hydrated = self._hydrate_from_snapshot(
                episode_id=resolved_episode_id,
                session_id=resolved_session_id,
                task_level=resolved_task_level,
            )
            if not hydrated:
                self.reset(
                    episode_id=resolved_episode_id,
                    task_level=resolved_task_level,
                    session_id=resolved_session_id,
                )

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
                case_id=(self._state.episode_id or "")[:8],
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

        precedents = self._precedent_engine.get_relevant_precedents(
            self._case["case_type"],
            self._case["key_facts"],
            exclude_case_id=(self._state.episode_id or "")[:8],
        )

        self._persist_snapshot()

        return self._build_observation(
            reward=step_score,
            step_score=step_score,
            final_score=final_score,
            feedback=feedback,
            precedents=precedents,
        )

    @property
    def state(self) -> State:
        return self._state
