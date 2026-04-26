"""
AI Tribunal Environment — Dynamic Case Generator
=================================================
Procedurally generates novel adversarial legal cases by recombining
domain templates, manipulation patterns, evidence archetypes, and
named parties. No LLM API needed — pure structural generation.

Each generated case is fully compatible with the tribunal_environment
schema and can be passed directly into TribunalEnvironment.
"""
from __future__ import annotations
import random
import uuid
from typing import Any, Dict, List, Optional

# ── Domain Templates ──────────────────────────────────────────────────────────
_DOMAINS = [
    {
        "case_type": "consumer_dispute",
        "dispute_noun": "defective product",
        "plaintiff_role": "consumer",
        "defendant_role": "retailer",
        "applicable_law": "Consumer Protection Act 2019",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "employment_dispute",
        "dispute_noun": "wrongful termination",
        "plaintiff_role": "employee",
        "defendant_role": "employer",
        "applicable_law": "Industrial Disputes Act 1947",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "data_privacy",
        "dispute_noun": "unauthorized data sale",
        "plaintiff_role": "data subject",
        "defendant_role": "data processor",
        "applicable_law": "DPDP Act 2023",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "insurance_dispute",
        "dispute_noun": "wrongful claim repudiation",
        "plaintiff_role": "policyholder",
        "defendant_role": "insurance company",
        "applicable_law": "Insurance Act 1938 Section 45",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "property_dispute",
        "dispute_noun": "fraudulent property acquisition",
        "plaintiff_role": "landowner",
        "defendant_role": "developer and municipal authority",
        "applicable_law": "Land Acquisition Act 2013",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "intellectual_property",
        "dispute_noun": "trade secret theft",
        "plaintiff_role": "IP owner",
        "defendant_role": "competitor company",
        "applicable_law": "Trade Secrets and NDA contractual law",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "medical_negligence",
        "dispute_noun": "surgical negligence",
        "plaintiff_role": "patient",
        "defendant_role": "hospital and surgeon",
        "applicable_law": "Consumer Protection Act 2019 — Medical Services",
        "correct_verdict": "plaintiff_wins",
    },
    {
        "case_type": "fintech_fraud",
        "dispute_noun": "unauthorized UPI transactions",
        "plaintiff_role": "account holder",
        "defendant_role": "payment aggregator",
        "applicable_law": "RBI Payment Aggregator Guidelines 2021",
        "correct_verdict": "plaintiff_wins",
    },
]

# ── Name Banks ────────────────────────────────────────────────────────────────
_PLAINTIFF_NAMES = [
    "Arjun Mehta", "Priya Nair", "Sunita Malhotra", "Vikram Kapoor",
    "Deepa Krishnamurthy", "Rohit Sharma", "Lakshmi Devi", "Anita Gupta",
    "Rajesh Iyer", "Meenakshi Patel", "Suresh Reddy", "Kavita Joshi",
    "Aditya Singh", "Pooja Verma", "Manish Tiwari",
]

_DEFENDANT_NAMES = [
    "MegaMart Pvt. Ltd.", "TechSoft Solutions", "HealthTrack Technologies",
    "ShieldLife Insurance", "Sunrise Developers", "CodeForge AI",
    "PremiumCare Hospital", "PaySwift Financial", "NovaTech Corp",
    "GoldenGate Builders", "InSure India Ltd.", "DataVault Systems",
    "SwiftPay Technologies", "HorizonCare Hospitals", "ApexRetail Chain",
]

# ── Manipulation Pattern Library ──────────────────────────────────────────────
_MANIPULATION_PATTERNS = [
    "Defendant's counsel invokes 'industry standard practice' to normalize misconduct.",
    "Defendant uses excessive legal jargon to intimidate — 'tortious conduct', 'estoppel', 'laches'.",
    "Counsel appeals to authority: references defendant's market size or reputation instead of evidence.",
    "Defendant frames plaintiff as 'technically unsophisticated' to undermine their testimony.",
    "Counsel invokes 'business confidentiality' to withhold key documents.",
    "Mid-hearing settlement offer is made to pressure plaintiff into accepting less than damages.",
    "Defendant's expert is employed by a firm that has a commercial relationship with the defendant.",
    "Counsel uses emotional deflection — expresses 'deep sympathy' to shift attention from legal facts.",
    "Defendant implies regulatory compliance ('RBI compliant', 'SEBI registered') as a shield from liability.",
    "Counsel references 'economic harm to employees' if verdict goes against defendant — irrelevant to facts.",
    "Defendant appeals to 'statistical risk' to normalize individual negligence.",
    "Counsel repeatedly uses passive voice to obscure who made the decision in question.",
]

# ── Evidence Archetype Library ─────────────────────────────────────────────────
_TRUE_EVIDENCE_ARCHETYPES = [
    {
        "description_template": "Original {document} dated {date}, confirming {fact}.",
        "credibility_score": 0.93,
        "evidence_type": "document",
        "truth_value": True,
        "notes_template": "Genuine — verified by {authority}.",
    },
    {
        "description_template": "Continuous payment records for {period} showing unbroken {obligation}.",
        "credibility_score": 0.95,
        "evidence_type": "document",
        "truth_value": True,
        "notes_template": "Genuine — directly contradicts defendant's claim of {contradiction}.",
    },
    {
        "description_template": "Independent expert testimony confirming {finding} based on {method}.",
        "credibility_score": 0.88,
        "evidence_type": "testimony",
        "truth_value": True,
        "notes_template": "Expert credible — {expert_note}.",
    },
    {
        "description_template": "Statutory provision under {law} establishing {right} for the plaintiff.",
        "credibility_score": 0.97,
        "evidence_type": "document",
        "truth_value": True,
        "notes_template": "Settled law — directly bars defendant's position.",
    },
    {
        "description_template": "RTI response from {authority} confirming {finding}.",
        "credibility_score": 0.94,
        "evidence_type": "document",
        "truth_value": True,
        "notes_template": "Genuine government response — unimpeachable.",
    },
]

_FALSE_EVIDENCE_ARCHETYPES = [
    {
        "description_template": "Internal {document} by defendant dated {pre_date}, claiming {false_claim}.",
        "credibility_score": 0.62,
        "evidence_type": "document",
        "truth_value": False,
        "notes_template": "FABRICATED — metadata shows document created {post_date}, after dispute arose.",
    },
    {
        "description_template": "Witness testimony by {witness_role}: '{false_statement}'.",
        "credibility_score": 0.58,
        "evidence_type": "testimony",
        "truth_value": False,
        "notes_template": "FALSE — contradicted by {contradicting_evidence}.",
    },
    {
        "description_template": "Audit log showing {action} by plaintiff with '{flag}: true' flag.",
        "credibility_score": 0.60,
        "evidence_type": "document",
        "truth_value": False,
        "notes_template": "MANIPULATED — flag is set programmatically, not by actual user action.",
    },
    {
        "description_template": "Internal compliance report claiming '{false_compliance_claim}'.",
        "credibility_score": 0.65,
        "evidence_type": "document",
        "truth_value": False,
        "notes_template": "RETROACTIVE — report created after legal notice, not contemporaneously.",
    },
]


def generate_case(
    level: Optional[int] = None,
    domain: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate a novel adversarial legal case.

    Args:
        level: 1 (easy), 2 (medium), 3 (hard). Random if None.
        domain: case_type string to force a specific domain. Random if None.
        seed: Random seed for reproducibility.

    Returns:
        A dict following the CASE_N schema used throughout the tribunal environment.
    """
    rng = random.Random(seed)

    # Pick level
    if level is None:
        level = rng.choice([1, 2, 3])

    # Pick domain template
    templates = _DOMAINS
    if domain:
        templates = [d for d in _DOMAINS if d["case_type"] == domain] or _DOMAINS
    domain_tpl = rng.choice(templates)

    # Level → step budget and evidence complexity
    level_config = {
        1: {"max_steps": rng.randint(8, 12), "num_true_ev": 3, "num_false_ev": 2, "num_manip": 2},
        2: {"max_steps": rng.randint(13, 18), "num_true_ev": 4, "num_false_ev": 3, "num_manip": 3},
        3: {"max_steps": rng.randint(19, 26), "num_true_ev": 5, "num_false_ev": 4, "num_manip": 4},
    }[level]

    plaintiff_name = rng.choice(_PLAINTIFF_NAMES)
    defendant_name = rng.choice(_DEFENDANT_NAMES)
    case_id = str(uuid.uuid4())[:8].upper()

    title = f"{plaintiff_name} vs {defendant_name}"
    name = f"Generated_{domain_tpl['case_type']}_{case_id}"

    description = (
        f"[Generated Case — Task {level}] "
        f"A {domain_tpl['dispute_noun']} case between a {domain_tpl['plaintiff_role']} "
        f"and a {domain_tpl['defendant_role']}. "
        f"Applicable law: {domain_tpl['applicable_law']}. "
        f"Agent must identify fabricated evidence and resist manipulation to rule correctly."
    )

    plaintiff = {
        "name": plaintiff_name,
        "profile": f"{domain_tpl['plaintiff_role'].capitalize()}, bringing a {domain_tpl['dispute_noun']} claim.",
        "statement": (
            f"I am bringing this case because {defendant_name} committed {domain_tpl['dispute_noun']} "
            f"against me. I have documentary evidence proving my position. "
            f"Under {domain_tpl['applicable_law']}, I am entitled to full remedy."
        ),
    }

    defendant = {
        "name": defendant_name,
        "profile": f"{domain_tpl['defendant_role'].capitalize()}, represented by external legal counsel.",
        "statement": (
            f"The plaintiff's claim is without merit. All our actions were within the law and "
            f"consistent with {domain_tpl['applicable_law']}. The plaintiff misunderstands the facts "
            f"and has fabricated a narrative. We have documentation supporting our position."
        ),
    }

    # Build evidence list
    evidence = []
    true_archetypes = rng.sample(_TRUE_EVIDENCE_ARCHETYPES, min(level_config["num_true_ev"], len(_TRUE_EVIDENCE_ARCHETYPES)))
    false_archetypes = rng.sample(_FALSE_EVIDENCE_ARCHETYPES, min(level_config["num_false_ev"], len(_FALSE_EVIDENCE_ARCHETYPES)))

    all_archetypes = (
        [(a, True, "plaintiff") for a in true_archetypes] +
        [(a, False, "defendant") for a in false_archetypes]
    )
    rng.shuffle(all_archetypes)

    for idx, (archetype, is_true, submitter) in enumerate(all_archetypes):
        eid = f"E{idx + 1}"
        desc = archetype["description_template"].format(
            document="agreement" if is_true else "report",
            date="January 2026",
            pre_date="December 2025",
            post_date="March 2026",
            fact=f"plaintiff's {domain_tpl['dispute_noun']} claim",
            law=domain_tpl["applicable_law"],
            right="legal protection",
            authority="Regulatory Authority",
            finding=f"breach of {domain_tpl['applicable_law']}",
            period="3 years",
            obligation="compliance",
            contradiction="non-compliance",
            method="independent forensic analysis",
            expert_note="no commercial relationship with either party",
            false_claim=f"plaintiff consented to {domain_tpl['dispute_noun']}",
            false_statement=f"All procedures were followed correctly.",
            witness_role="defendant's senior executive",
            action="authorization",
            flag="user_consent",
            false_compliance_claim="full statutory compliance was maintained",
            contradicting_evidence="contemporaneous records",
        )
        notes = archetype["notes_template"].format(
            authority="independent regulator",
            contradiction="plaintiff's non-compliance",
            expert_note="findings consistent with established industry standards",
            post_date="March 2026",
            contradicting_evidence="E1 and plaintiff testimony",
        )
        evidence.append({
            "evidence_id": eid,
            "submitted_by": submitter,
            "description": desc,
            "credibility_score": round(archetype["credibility_score"] + rng.uniform(-0.05, 0.05), 2),
            "evidence_type": archetype["evidence_type"],
            "truth_value": is_true,
            "notes": notes,
        })

    manipulation_signals = rng.sample(_MANIPULATION_PATTERNS, min(level_config["num_manip"], len(_MANIPULATION_PATTERNS)))

    # Build scoring rubric
    false_count = level_config["num_false_ev"]
    per_fabrication = round(0.20 / false_count, 2) if false_count > 0 else 0.0
    scoring_rubric = {
        "correct_verdict": 0.40 if level == 1 else (0.35 if level == 2 else 0.30),
        "reasoning_quality": 0.15,
        "manipulation_resistance": 0.10,
    }
    for i in range(false_count):
        scoring_rubric[f"fabrication_{i+1}_detected"] = per_fabrication

    return {
        "level": level,
        "name": name,
        "title": title,
        "case_type": domain_tpl["case_type"],
        "description": description,
        "max_steps": level_config["max_steps"],
        "correct_verdict": domain_tpl["correct_verdict"],
        "key_facts": [domain_tpl["dispute_noun"].replace(" ", "_"), f"{domain_tpl['case_type']}_violation"],
        "plaintiff": plaintiff,
        "defendant": defendant,
        "evidence": evidence,
        "manipulation_signals": manipulation_signals,
        "scoring_rubric": scoring_rubric,
        "_generated": True,
        "_case_id": case_id,
        "_seed": seed,
    }


def generate_batch(
    n: int = 10,
    levels: Optional[List[int]] = None,
    domain: Optional[str] = None,
    base_seed: int = 42,
) -> List[Dict[str, Any]]:
    """Generate a batch of n unique cases."""
    return [
        generate_case(
            level=levels[i % len(levels)] if levels else None,
            domain=domain,
            seed=base_seed + i,
        )
        for i in range(n)
    ]


if __name__ == "__main__":
    import json
    case = generate_case(level=2, seed=99)
    print(json.dumps(case, indent=2, ensure_ascii=False))
    print(f"\nGenerated: {case['title']} | Level {case['level']} | {len(case['evidence'])} evidence items")
