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

## 📌 Submission Links
- **Hugging Face Space:** [https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
- **GitHub Repository:** [https://github.com/AbhishekKharat04/ai-tribunal-env](https://github.com/AbhishekKharat04/ai-tribunal-env)
- **Training Notebook:** [AI Tribunal — GRPO Training (Kaggle)](https://www.kaggle.com/code/abhishekkharat04/ai-tribunal-grpo-training)
- **Blog Post:** [blog.md](blog.md) (Included in repo)

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

## 📈 Training Results

After training the 1.5B parameter Qwen2.5 model using GRPO (with the custom training script provided in the notebook), the model successfully learned to navigate the environment and improve its reasoning and verdicts:

- **Initial Average Reward:** ~0.45
- **Final Average Reward:** ~0.68
- **Improvement:** +0.23 (51.1%)

### Final Task Scores (Trained Model)
- **Task 1 (Consumer - Easy):** 0.720
- **Task 2 (Employment - Medium):** 0.685
- **Task 3 (Property - Hard):** 0.650

The model demonstrated a clear ability to detect fabricated evidence and align its rulings with established precedents.

![Training reward curve](reward_curve.png)
*Reward improves over training episodes with the trained policy interacting against the live environment.*

![Task score curves](task_scores.png)
*Task-level evaluation of the trained model across all three benchmark tasks.*

---

## 🚀 Quick Start

```python
import requests
import uuid

BASE = "https://abhishekkharat11-ai-tribunal-env.hf.space"
session_id = f"demo-{uuid.uuid4()}"

# Start a case using the standard OpenEnv HTTP API.
# Because HTTP requests are stateless, pass session + episode IDs back into /step.
reset = requests.post(
    f"{BASE}/reset",
    json={"task_level": 2, "session_id": session_id},
).json()
obs = reset["observation"]
episode_id = obs["episode_id"]
print(obs["case_title"])

# Take an action
result = requests.post(
    f"{BASE}/step",
    json={
        "session_id": session_id,
        "episode_id": episode_id,
        "task_level": 2,
        "action": {
            "action_type": "examine_evidence",
            "reasoning": "I will examine evidence E3 because its timing and metadata are suspicious relative to the HR complaint and the sudden performance narrative...",
            "target": "E3",
            "evidence_reliability_assessments": {"E3": 0.2}
        }
    }
).json()

# Issue a ruling
result = requests.post(
    f"{BASE}/step",
    json={
        "session_id": session_id,
        "episode_id": episode_id,
        "task_level": 2,
        "action": {
            "action_type": "rule",
            "reasoning": "Based on examination, the fabricated evidence and procedural violations outweigh the defendant's unsupported narrative...",
            "verdict": "plaintiff_wins",
            "verdict_reasoning": "The defendant's performance log was created retroactively, the panel was not independent, and the mandatory PIP requirement was ignored...",
            "evidence_reliability_assessments": {"E3": 0.15, "E6": 0.25}
        }
    }
).json()

print(f"Score: {result['observation']['step_score']}")
```

For the browser demo, use the custom game UI at `/` which manages a session automatically through `/game/reset` and `/game/step`.

---

## Agent Access

The Space now exposes a lightweight agent wrapper at [`/agents.md`](https://abhishekkharat11-ai-tribunal-env.hf.space/agents.md) so external coding agents can discover the API quickly.

- Use `/game/reset` + `/game/step` for the simplest tool-style integration.
- Use `/reset` + `/step` if you want the standard OpenEnv HTTP contract.
- Reuse the same `session_id` across related cases when you want precedent consistency to carry forward.

**About the Hugging Face “Agents” button:** Hugging Face’s current documentation says that header integration is auto-exposed for compatible **Gradio** Spaces. This project is a **Docker Space**, so not having that button does **not** make the submission incomplete. The manual `/agents.md` wrapper keeps the Space agent-friendly even without the built-in Gradio header integration.

---

## 🇮🇳 Real-World Impact

- India has **over 50 million pending court cases**
- Fast-track tribunals handle millions of consumer, employment, and property disputes annually
- LLMs trained on this environment learn adversarial reasoning skills transferable to real legal assistance

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start a standard OpenEnv session; returns `session_id` and `episode_id` in the observation |
| `/step` | POST | Take an action in a stateless HTTP call by passing `session_id` + `episode_id` back |
| `/state` | GET | Current state |
| `/tasks` | GET | All 3 tasks + action schema |
| `/grader` | POST | Grade an action |
| `/baseline` | GET | Run baseline agent |
| `/game/reset` | POST | Start a browser/game session |
| `/game/step` | POST | Continue a browser/game session |
| `/agents.md` | GET | Plain-text wrapper for external coding agents and tool discovery |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |

---

*Built for Meta PyTorch OpenEnv Hackathon × Scaler SST — Solo entry by Abhishek Kharat*
