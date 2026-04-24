"""
AI Tribunal Environment — Precedent Consistency Engine

THE KEY MECHANIC:
Stores past rulings and penalises the agent when it rules inconsistently
with its own precedents on similar cases. This tests something LLMs
fundamentally fail at: maintaining consistent internal jurisprudence.

Deliberately kept simple and deterministic — no ML, no embeddings.
Matching is fact-overlap based for reliability and trainability.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class PrecedentRecord:
    case_id: str
    case_type: str
    key_facts: List[str]
    verdict: str
    step: int
    task_level: int


class PrecedentEngine:
    """
    Stores verdicts and detects consistency violations.

    Two rulings are "similar" if they share the same case_type
    AND have ≥2 overlapping key facts.

    Consistency reward:  +0.3 if verdict matches similar precedent
    Inconsistency penalty: -0.3 if verdict contradicts similar precedent
    """

    def __init__(self):
        self._records: List[PrecedentRecord] = []
        self._consistency_violations: int = 0
        self._consistency_confirmations: int = 0

    def add_verdict(
        self,
        case_id: str,
        case_type: str,
        key_facts: List[str],
        verdict: str,
        step: int,
        task_level: int,
    ) -> Tuple[float, str]:
        """
        Record a new verdict and return (consistency_reward, feedback).
        """
        similar = self._find_similar(case_type, key_facts, exclude_case_id=case_id)

        reward = 0.0
        feedback_lines = []

        if similar:
            prev = similar[0]
            overlap = self._fact_overlap(key_facts, prev.key_facts)
            if prev.verdict == verdict:
                reward = 0.30
                self._consistency_confirmations += 1
                feedback_lines.append(
                    f"✅ PRECEDENT CONSISTENT: Ruling '{verdict}' aligns with "
                    f"'{prev.case_id}' ({prev.case_type}, {overlap} shared facts). (+0.30)"
                )
            else:
                reward = -0.30
                self._consistency_violations += 1
                feedback_lines.append(
                    f"❌ PRECEDENT VIOLATED: Ruling '{verdict}' contradicts "
                    f"'{prev.case_id}' which ruled '{prev.verdict}' "
                    f"on similar facts ({overlap} shared: {overlap}). (-0.30) "
                    "Inconsistent jurisprudence detected."
                )
        else:
            feedback_lines.append(
                "ℹ️  No similar precedent found — this ruling sets a new precedent."
            )

        self._records.append(PrecedentRecord(
            case_id=case_id,
            case_type=case_type,
            key_facts=key_facts,
            verdict=verdict,
            step=step,
            task_level=task_level,
        ))

        return reward, "\n".join(feedback_lines)

    def get_relevant_precedents(
        self, case_type: str, key_facts: List[str], exclude_case_id: str = ""
    ) -> List[Dict]:
        """Return formatted precedents for the agent's observation."""
        similar = self._find_similar(case_type, key_facts, exclude_case_id)
        return [
            {
                "case_id": r.case_id,
                "case_type": r.case_type,
                "shared_facts": self._fact_overlap(key_facts, r.key_facts),
                "verdict": r.verdict,
                "task_level": r.task_level,
            }
            for r in similar
        ]

    def get_consistency_score(self) -> float:
        """Returns a 0.0-1.0 consistency score for the episode."""
        total = self._consistency_violations + self._consistency_confirmations
        if total == 0:
            return 1.0
        return round(self._consistency_confirmations / total, 3)

    def reset(self):
        self._records.clear()
        self._consistency_violations = 0
        self._consistency_confirmations = 0

    def _find_similar(
        self, case_type: str, key_facts: List[str], exclude_case_id: str = ""
    ) -> List[PrecedentRecord]:
        similar = []
        for r in self._records:
            if r.case_id == exclude_case_id:
                continue
            if r.case_type != case_type:
                continue
            overlap = self._fact_overlap(key_facts, r.key_facts)
            if overlap >= 2:
                similar.append(r)
        # Most recent first
        return list(reversed(similar))

    @staticmethod
    def _fact_overlap(facts_a: List[str], facts_b: List[str]) -> int:
        return len(set(facts_a) & set(facts_b))
