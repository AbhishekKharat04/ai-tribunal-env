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

> **An RL environment where AI agents learn to judge adversarial legal cases — detecting fabricated evidence, resisting manipulation, and maintaining consistent jurisprudence across episodes.**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/meta-pytorch/OpenEnv)

---

## 📌 Submission Links

| Asset | Link |
|-------|------|
| **Live Environment (HF Space)** | [huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env) |
| **GitHub Repository** | [github.com/AbhishekKharat04/ai-tribunal-env](https://github.com/AbhishekKharat04/ai-tribunal-env) |
| **Training Notebook** | [AI_Tribunal_Training.ipynb](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/AI_Tribunal_Training.ipynb) |
| **Training Script** | [train_tribunal_grpo.py](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/train_tribunal_grpo.py) |
| **Blog / Writeup** | [blog.md](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/blog.md) |

---

## 🧑‍⚖️ What Is This?

Most RL environments test knowledge or reflexes. **AI Tribunal tests judgment under conflict.**

The agent acts as a judge in adversarial legal disputes. Evidence can be fabricated, parties use manipulation tactics, and similar cases must be ruled consistently. The environment rewards agents that:

- **Detect fabricated evidence** — high credibility ≠ truth
- **Resist manipulation** — intimidation, emotional deflection, jargon overload
- **Maintain precedent consistency** — contradicting your own prior rulings is penalized

---

## 🔑 Core Mechanics

### 1. Evidence Reliability Scoring
Every evidence item has a hidden truth value and a visible credibility score. High-credibility evidence can be fabricated. Low-credibility evidence can be true. The agent must learn that **confidence does not equal truth**.

### 2. Precedent Consistency Engine
The agent's past rulings are stored. When it encounters a similar case, it gets a consistency bonus or penalty. This tests **cross-episode jurisprudential reasoning** rather than one-off classification.

### 3. Adversarial Manipulation
Parties actively try to manipulate the judge — withholding evidence, using intimidation, invoking procedural pressure. The agent is rewarded for **detecting and resisting** these attempts.

---

## 📋 Benchmark Cases

8 curated adversarial hearings + an **infinite procedural case generator** for fresh randomized disputes.

| # | Case | Domain | Difficulty |
|---|------|--------|------------|
| 1 | Sharma vs MegaMart | Consumer dispute | Easy |
| 2 | Meenakshi Iyer vs TechSoft | Employment dispute | Medium |
| 3 | Lakshmi Devi vs Sunrise Developers | Property fraud | Hard |
| 4 | Priya Nair vs HealthTrack App | Data privacy (DPDP Act) | Easy-Medium |
| 5 | Vikram Malhotra vs ShieldLife Insurance | Insurance fraud | Medium |
| 6 | NeuralDraft Ltd. vs CodeForge AI | IP / Trade secret theft | Medium |
| 7 | Arjun Kapoor vs PremiumCare Hospital | Medical negligence | Hard |
| 8 | Deepa Menon vs PaySwift Financial | Fintech / UPI fraud | Hard |

The dynamic case generator (`server/case_generator.py`) can produce unlimited novel cases by recombining domain templates, manipulation patterns, and evidence archetypes.

---

## 📊 Training Results

Training was performed using **GRPO (Group Relative Policy Optimization)** via the TRL library on a Kaggle T4 GPU. All plots below are committed directly in this repository.

![Reward and task-score curves from GRPO training](reward_curve.png)

![Training loss curve](loss_curve.png)

---

## 🚀 Quick Start for Judges

**You do not need to install anything.** Just open the Space:

1. Go to the [Live Environment](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
2. Pick a case (Easy → Hard)
3. Use the built-in guided tour or the `?` help button
4. Inspect evidence, question parties, issue your ruling
5. The environment scores you on verdict accuracy, evidence detection, and manipulation resistance

---

## 🔌 API Quick Start

```python
import requests, uuid

BASE = "https://abhishekkharat11-ai-tribunal-env.hf.space"
session_id = f"demo-{uuid.uuid4()}"

# Reset
reset = requests.post(f"{BASE}/reset", json={"task_level": 2, "session_id": session_id}).json()
obs = reset["observation"]

# Take an action
result = requests.post(f"{BASE}/step", json={
    "session_id": session_id,
    "episode_id": obs["episode_id"],
    "task_level": 2,
    "action": {
        "action_type": "examine_evidence",
        "reasoning": "Examining E3 — timing and metadata are suspicious.",
        "target": "E3",
        "evidence_reliability_assessments": {"E3": 0.2}
    }
}).json()

print(result["observation"]["step_score"])
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start a new OpenEnv session |
| `/step` | POST | Take an action (examine, question, rule) |
| `/state` | GET | Current environment state |
| `/tasks` | GET | Task catalog + action schema |
| `/game/reset` | POST | Start a browser game session |
| `/game/step` | POST | Continue a browser game session |
| `/game/generate` | POST | Generate a random procedural case |
| `/game/cojudge` | POST | Ask the AI Co-Judge for guidance |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive Swagger UI |

---

## 🏗️ Architecture

```
tribunal_env/
├── server/
│   ├── app.py                    # FastAPI routes (OpenEnv + game UI)
│   ├── tribunal_environment.py   # Core RL environment (BaseEnv)
│   ├── cases.py                  # 8 curated adversarial cases
│   ├── case_generator.py         # Procedural case generator
│   ├── grader.py                 # Multi-dimensional reward grading
│   ├── precedent_engine.py       # Cross-episode consistency tracker
│   └── ai_judge.py               # HF inference-backed Co-Judge
├── static/                       # Courtroom web UI (HTML/CSS/JS)
├── models.py                     # Pydantic action/observation schemas
├── train_tribunal_grpo.py        # GRPO training script (TRL)
├── AI_Tribunal_Training.ipynb    # Jupyter notebook version
├── blog.md                       # Project writeup
├── openenv.yaml                  # OpenEnv manifest
├── Dockerfile                    # Container definition for HF Space
└── pyproject.toml                # Package definition
```

---

*Built for the Meta PyTorch OpenEnv Hackathon 2026 by Abhishek Kharat.*
