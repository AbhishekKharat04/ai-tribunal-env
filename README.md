---
title: AI Tribunal Environment
emoji: ⚖️
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: true
tags:
  - openenv
  - legal-reasoning
  - adversarial
---

# ⚖️ AI Tribunal Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/meta-pytorch/OpenEnv)

> **An RL training environment where AI agents learn to judge adversarial legal cases — detecting fabricated evidence, resisting manipulation, and maintaining consistent jurisprudence across episodes.**

---

## 🧠 What Makes This Different

Most RL environments test knowledge or reflexes. This environment tests **judgment under conflict**.

Three unique mechanics no other environment has:

### 1. 🔍 Evidence Reliability Scoring
Each evidence item has a **hidden truth value** and a **visible credibility score**. High-credibility evidence can be fabricated. Low-credibility evidence can be true. The agent must learn that **confidence ≠ truth**.

### 2. ⚖️ Precedent Consistency Engine
The agent's past rulings are stored. When it encounters a similar case, it gets **+0.30** for consistency and **-0.30** for contradiction. This tests cross-episode jurisprudential reasoning — something current LLMs completely fail at.

### 3. 🎭 Adversarial Manipulation
Parties actively try to manipulate the judge — withholding evidence, using intimidation tactics, offering mid-hearing settlements, invoking political connections. The agent is rewarded for detecting and resisting these attempts.

---

## 🎯 Three Tasks

| Task | Case | Difficulty | Steps | Key Challenge |
|------|------|------------|-------|---------------|
| 1 | Sharma vs MegaMart (Consumer) | Easy | 8 | Fabricated inspection report + nonexistent CCTV |
| 2 | Meenakshi Iyer vs TechSoft (Employment) | Medium | 15 | Retroactive performance docs + biased HR panel |
| 3 | Lakshmi Devi vs Sunrise Developers (Property) | Hard | 25 | Forged acquisition + corrupt official + political pressure |

---

## 📊 Reward Formula

```
Verdict correctness:     0.40
Evidence detection:      0.20  (fabrications correctly identified)
Precedent consistency:   0.20  (from Precedent Engine)
Manipulation resistance: 0.10
Reasoning quality:       0.10
─────────────────────────────
Total:                   1.00
```

---

## 🚀 Quick Start

```python
import requests

BASE = "https://abhishekkharat11-ai-tribunal-env.hf.space"

# Start a case
obs = requests.post(f"{BASE}/reset", json={}).json()["observation"]
print(obs["case_title"])

# Take an action
result = requests.post(f"{BASE}/step", json={"action": {
    "action_type": "examine_evidence",
    "reasoning": "I will examine evidence E3 which has suspicious timing relative to the HR complaint...",
    "target": "E3",
    "evidence_reliability_assessments": {"E3": 0.2}
}}).json()

# Issue a ruling
result = requests.post(f"{BASE}/step", json={"action": {
    "action_type": "rule",
    "reasoning": "Based on examination, the fabricated evidence and procedural violations...",
    "verdict": "plaintiff_wins",
    "verdict_reasoning": "The defendant's performance log was created retroactively...",
    "evidence_reliability_assessments": {"E3": 0.15, "E6": 0.25}
}}).json()

print(f"Score: {result['observation']['step_score']}")
```

---

## 🇮🇳 Real-World Impact

- India has **45 million pending court cases**
- Fast-track tribunals handle millions of consumer, employment, and property disputes annually
- LLMs trained on this environment learn adversarial reasoning skills transferable to real legal assistance

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start new case |
| `/step` | POST | Take action |
| `/state` | GET | Current state |
| `/tasks` | GET | All 3 tasks + action schema |
| `/grader` | POST | Grade an action |
| `/baseline` | GET | Run baseline agent |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |

---

*Built for Meta PyTorch OpenEnv Hackathon × Scaler SST — Solo entry by Abhishek Kharat*
