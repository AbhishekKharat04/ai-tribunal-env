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

# AI Tribunal — Teaching AI to Judge Fair

**By Abhishek Kharat | Meta PyTorch OpenEnv Hackathon 2026**

**Try it live →** [https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)

---

## The Problem I Wanted to Solve

India has over **4.7 crore pending court cases**. Some of them have been waiting for 10, 20, even 30 years. I've heard stories from family and neighbours about how a simple consumer complaint or a property dispute can drag on for years, not because the facts are complicated, but because the system gets overwhelmed, evidence gets manipulated, and nobody catches it in time.

I started thinking — what if AI could help? Not replace judges, but assist them. Help them spot when a document was backdated, when a witness statement contradicts the timeline, when one side is using intimidation to pressure a ruling. The kind of things that a tired human might miss after reviewing 50 cases in a day.

But here's the thing — you can't just ask an LLM "is this evidence fake?" and expect a good answer. The model needs to learn *how* to think through conflicting information, not just pattern-match. That's what reinforcement learning is for. And that's exactly what this environment does.

---

## What This Environment Does

AI Tribunal is an RL environment built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework. The agent plays the role of a tribunal judge in adversarial legal disputes.

Each case has:
- **A plaintiff and a defendant** with their own statements and evidence
- **Fabricated evidence** mixed in with real evidence — the agent doesn't know which is which
- **Manipulation tactics** — the defendant's lawyer might use jargon to confuse, appeal to emotion, or pressure the judge with irrelevant arguments
- **A correct verdict** that the agent needs to reach through reasoning, not guessing

The agent can take actions like:
- **Examine evidence** — inspect a specific document or testimony
- **Question the plaintiff** — press for details when something doesn't add up
- **Question the defendant** — challenge evasive or suspicious claims
- **Rule** — deliver a verdict with written reasoning

The environment scores the agent on multiple dimensions:
1. **Did you get the verdict right?**
2. **Did you identify the fabricated evidence?**
3. **Did you resist the manipulation signals?**
4. **Is your reasoning actually sound?**
5. **Are you consistent with your previous rulings in similar cases?**

That last one is important. In real courts, inconsistent rulings on similar facts is a serious problem. So the environment tracks precedent across cases in a session, and penalizes the agent if it contradicts itself.

---

## The Cases

I started with 3 cases during initial development, but quickly realized that wasn't enough for a proper benchmark. So I expanded it to **8 curated cases** covering different areas of Indian law, plus a **dynamic case generator** that can produce unlimited new cases on the fly.

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

Each case has its own set of manipulation patterns. For example, in Case 5 (insurance), the defendant's lawyer tries to invoke "industry standard practice" to normalize what is essentially fraud. In Case 7 (medical negligence), pages from the patient's chart conveniently go missing. The agent has to catch these things.

The dynamic case generator (`server/case_generator.py`) recombines domain templates, evidence archetypes, and manipulation signals to create fresh disputes every time. This means the benchmark never runs out of data — an agent can't just memorize the 8 curated cases and call it a day.

---

## How I Trained It

I used **GRPO (Group Relative Policy Optimization)** from the TRL library. The idea is simple — generate multiple candidate responses for the same case, score them using the environment's reward function, and update the model to prefer the better responses.

The training script is [`train_tribunal_grpo.py`](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/train_tribunal_grpo.py) and the notebook version is [`AI_Tribunal_Training.ipynb`](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/AI_Tribunal_Training.ipynb). I ran it on a Kaggle T4 GPU. It's not a massive compute run — I wanted to prove the concept works, not burn through credits.

Here are the actual training curves from that run:

![Reward and task-score curves](reward_curve.png)

![Loss curve](loss_curve.png)

The reward improved from 0.200 to 0.203 over the run. That's small, but it's real — the model is learning to make slightly better decisions each episode. With more compute and a longer run, this would improve significantly. The important thing is that the training loop works end-to-end: the environment serves cases, the model generates responses, the grader scores them, and the model updates.

---

## Try It Yourself

The easiest way to see what this does is to just open the Space and play a case:

1. Go to [the live environment](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
2. Pick any case — I'd suggest starting with Case 1 (Easy)
3. A guided tour will walk you through the courtroom interface
4. Read both sides, inspect the evidence, look for inconsistencies
5. When you're ready, issue your ruling with reasoning

No installation needed. It runs in the browser.

If you want to call the API directly:

```python
import requests, uuid

BASE = "https://abhishekkharat11-ai-tribunal-env.hf.space"
session_id = f"demo-{uuid.uuid4()}"

reset = requests.post(f"{BASE}/reset", json={"task_level": 2, "session_id": session_id}).json()
obs = reset["observation"]

result = requests.post(f"{BASE}/step", json={
    "session_id": session_id,
    "episode_id": obs["episode_id"],
    "task_level": 2,
    "action": {
        "action_type": "examine_evidence",
        "reasoning": "E3 looks suspicious — the timing doesn't match the defendant's story.",
        "target": "E3",
        "evidence_reliability_assessments": {"E3": 0.2}
    }
}).json()

print(result["observation"]["step_score"])
```

---

## All Submission Materials

Everything is in this repository and linked below:

| What | Where |
|------|-------|
| Live environment (HF Space) | [huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env) |
| GitHub repo | [github.com/AbhishekKharat04/ai-tribunal-env](https://github.com/AbhishekKharat04/ai-tribunal-env) |
| Training notebook | [AI_Tribunal_Training.ipynb](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/AI_Tribunal_Training.ipynb) |
| Training script | [train_tribunal_grpo.py](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/train_tribunal_grpo.py) |
| Blog / writeup | [blog.md](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/blog.md) |
| Training curves | `reward_curve.png`, `loss_curve.png` (committed in repo) |
| OpenEnv manifest | `openenv.yaml` |

---

## Project Structure

```
tribunal_env/
├── server/
│   ├── app.py                    # FastAPI server (OpenEnv + game UI)
│   ├── tribunal_environment.py   # Core RL environment
│   ├── cases.py                  # 8 adversarial cases
│   ├── case_generator.py         # Dynamic case generator
│   ├── grader.py                 # Multi-factor reward grading
│   ├── precedent_engine.py       # Cross-case consistency
│   └── ai_judge.py               # AI Co-Judge (HF inference)
├── static/                       # Courtroom web UI
├── models.py                     # Pydantic schemas
├── train_tribunal_grpo.py        # GRPO training (TRL)
├── AI_Tribunal_Training.ipynb    # Notebook version
├── blog.md                       # Project writeup
├── openenv.yaml                  # OpenEnv manifest
├── Dockerfile                    # HF Space container
└── pyproject.toml                # Package config
```

---

*Built for the Meta PyTorch OpenEnv Hackathon 2026.*
