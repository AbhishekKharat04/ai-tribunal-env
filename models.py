"""
AI Tribunal Environment — Models
Typed Action/Observation for OpenEnv compliance.
"""
from typing import Optional, List, Dict, Any
from pydantic import Field
from openenv.core.env_server.types import Action, Observation


class TribunalAction(Action):
    """
    Action taken by the judge-agent each step.
    The agent must examine evidence, question parties,
    and ultimately issue a ruling.
    """
    action_type: str = Field(
        ...,
        description=(
            "One of: 'examine_evidence', 'question_plaintiff', "
            "'question_defendant', 'request_document', 'rule', 'adjourn'"
        ),
    )
    reasoning: str = Field(
        ...,
        description="Agent's explicit reasoning for this action (min 40 words).",
    )
    target: Optional[str] = Field(
        default=None,
        description="Evidence ID, party name, or document type to target.",
    )
    verdict: Optional[str] = Field(
        default=None,
        description=(
            "Final ruling when action_type='rule'. "
            "One of: 'plaintiff_wins', 'defendant_wins', 'partial_plaintiff', "
            "'partial_defendant', 'dismissed'."
        ),
    )
    verdict_reasoning: Optional[str] = Field(
        default=None,
        description="Full written judgment when issuing a ruling (min 60 words).",
    )
    evidence_reliability_assessments: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Agent's reliability scores for evidence items (0.0-1.0). "
            "Key = evidence_id, Value = assessed reliability."
        ),
    )


class EvidenceItem(Observation):
    """A single piece of evidence presented in the case."""
    evidence_id: str
    submitted_by: str          # "plaintiff" or "defendant"
    description: str
    credibility_score: float   # Visible to agent (0.0-1.0)
    evidence_type: str         # "document", "testimony", "photo", "contract"
    # truth_value is HIDDEN from agent — only used by grader
    # revealed in feedback after ruling


class TribunalObservation(Observation):
    """Full observation returned to the agent each step."""
    # Case basics
    case_id: str = Field(default="")
    episode_id: str = Field(default="")
    session_id: str = Field(default="")
    case_title: str = Field(default="")
    case_type: str = Field(default="")
    task_level: int = Field(default=1)
    task_name: str = Field(default="")

    # Parties
    plaintiff_statement: str = Field(default="")
    defendant_statement: str = Field(default="")
    plaintiff_profile: str = Field(default="")
    defendant_profile: str = Field(default="")

    # Evidence
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    manipulative_signals: List[str] = Field(
        default_factory=list,
        description="Signals that a party is attempting manipulation.",
    )

    # Precedents (key mechanic)
    relevant_precedents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Similar past rulings from this episode's case history.",
    )

    # Step tracking
    time_step: int = Field(default=0)
    max_steps: int = Field(default=10)
    done: bool = Field(default=False)

    # Feedback
    reward: float = Field(default=0.0)
    step_score: float = Field(default=0.0)
    cumulative_score: float = Field(default=0.0)
    final_score: Optional[float] = Field(default=None)
    feedback: str = Field(default="")

    # Metrics
    verdicts_issued: int = Field(default=0)
    consistency_score: float = Field(default=1.0)
    manipulation_resisted: int = Field(default=0)
    task_description: str = Field(default="")
