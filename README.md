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

# AI Tribunal Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/meta-pytorch/OpenEnv)

## Submission Links
- **Hugging Face Space:** [https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
- **GitHub Repository:** [https://github.com/AbhishekKharat04/ai-tribunal-env](https://github.com/AbhishekKharat04/ai-tribunal-env)
- **Training Notebook (repo):** [AI_Tribunal_Training.ipynb](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/AI_Tribunal_Training.ipynb)
- **Training Script:** [train_tribunal_grpo.py](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/train_tribunal_grpo.py)
- **Writeup / HF Blog Markdown:** [blog.md](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/blog.md)

## Submission Checklist
- Public Hugging Face Space: reachable at the submitted URL.
- Public GitHub repository: reachable at the submitted URL.
- OpenEnv manifest committed: `openenv.yaml`.
- Training artifacts currently committed in-repo: `reward_curve.png`, `task_scores.png`.
- Training script now emits `loss_curve.png` on the next rerun.
- Runnable training assets committed: `AI_Tribunal_Training.ipynb`, `train_tribunal_grpo.py`.
- Separate writeup markdown committed: `blog.md`.

## Final Submission Note

If the validator strictly requires both a reward curve and a loss curve as committed image files, the last remaining manual step is to rerun `train_tribunal_grpo.py` once and commit the generated `loss_curve.png`.

## Judge Quick Start

If you are evaluating the project, you do **not** need to run anything locally or download the linked models.

1. Open the Hugging Face Space.
2. Start with **Task 1 / Easy**.
3. Use the built-in guided tour or the `?` help button in the courtroom UI.
4. Inspect suspicious evidence, question the relevant side, then issue a ruling.

Local setup is only needed if you want to reproduce training runs or call the HTTP API directly.

> **An RL training environment where AI agents learn to judge adversarial legal cases - detecting fabricated evidence, resisting manipulation, and maintaining consistent jurisprudence across episodes.**

---

## Use Credits Wisely

Do **not** upgrade the current Space to GPU just to host the environment and UI. The benchmark server itself runs well on CPU unless you change it to load a model locally.

The best way to use your credits is:

1. Keep the Space on CPU for the courtroom game and environment API.
2. Use Hugging Face inference credits for the built-in `AI Co-Judge` helper.
3. Use Hugging Face Jobs / GPU credits for training or fine-tuning stronger models.
4. Use Cursor credits to accelerate code changes, refactors, data generation, and benchmark expansion - not as GPU compute.

### Enable the AI Co-Judge on the Space

Add these **Space secrets** in Hugging Face:

- `HF_TOKEN` = a fine-grained Hugging Face token with permission to call Inference Providers
- `AI_JUDGE_MODEL` = optional, defaults to `Qwen/Qwen2.5-72B-Instruct:fastest`
- `AI_JUDGE_MAX_CALLS_PER_SESSION` = optional, defaults to `3`

Once the Space restarts, judges can click **Ask AI Co-Judge** inside the courtroom. This uses inference credits only when requested, so it is much more efficient than paying for idle GPU hardware on the Space.

### Use HF GPU Credits for Training

The training script is also a UV script, so you can run it on Hugging Face Jobs:

```bash
hf jobs uv run --flavor a10g-large --timeout 4h --secrets HF_TOKEN train_tribunal_grpo.py
```

Optional environment variables:

- `ENV_URL` to point training at a different environment deployment
- `MODEL_NAME` to swap the base model
- `NUM_EPISODES`, `EVAL_EVERY`, `MAX_STEPS_PER_EPISODE`, `LEARNING_RATE`
- `PUSH_TO_HUB_REPO` to upload the resulting adapters and tokenizer automatically

### When a GPU Space does make sense

Upgrade the Space to GPU only if you later change the backend to load a local model directly inside the app process.

---

## What Makes This Different

Most RL environments test knowledge or reflexes. This environment tests **judgment under conflict**.

### 1. Evidence Reliability Scoring
Each evidence item has a hidden truth value and a visible credibility score. High-credibility evidence can be fabricated. Low-credibility evidence can be true. The agent must learn that confidence does not equal truth.

### 2. Precedent Consistency Engine
The agent's past rulings are stored. When it encounters a similar case, it gets a consistency bonus or penalty. This tests cross-episode jurisprudential reasoning rather than one-off case classification.

### 3. Adversarial Manipulation
Parties actively try to manipulate the judge by withholding evidence, using intimidation tactics, and invoking pressure. The agent is rewarded for detecting and resisting these attempts.

---

## Compared With Official Examples

The official [OpenEnv repo](https://github.com/meta-pytorch/OpenEnv) emphasizes a clean Gym-style `reset` / `step` / `state` contract, containerized deployment, and clear client-server separation. This project now follows that shape while targeting a more human-facing domain.

The official [TRL OpenEnv Sudoku example](https://github.com/huggingface/trl/blob/main/examples/notebooks/openenv_sudoku_grpo.ipynb) is a great reference for canonical `GRPOTrainer(..., environment_factory=...)` usage on a compact puzzle environment. AI Tribunal is different in two ways:

- It focuses on adversarial legal reasoning rather than a deterministic puzzle.
- It uses a lightweight custom rollout loop so the training script stays runnable on commodity Kaggle / Colab GPUs while still interacting with a live OpenEnv deployment.

If you are judging ambition rather than raw notebook length, this project is closer to a domain benchmark than a toy game clone.

---

## Three Tasks

| Task | Case | Difficulty | Steps | Key Challenge |
|------|------|------------|-------|---------------|
| 1 | Sharma vs MegaMart (Consumer) | Easy | 8 | Fabricated inspection report + nonexistent CCTV |
| 2 | Meenakshi Iyer vs TechSoft (Employment) | Medium | 15 | Retroactive performance docs + biased HR panel |
| 3 | Lakshmi Devi vs Sunrise Developers (Property) | Hard | 25 | Forged acquisition + corrupt official + political pressure |

---

## Training Artifacts

The repository includes committed training plots directly in the repo so validation does not depend on external dashboards or transient notebook outputs.

![Training reward curve](reward_curve.png)
*Reward curve committed in-repo.*

![Task score curves](task_scores.png)
*Task-level score plot committed in-repo.*

### Important note on the loss curve

The current committed training run does **not** yet include a checked-in `loss_curve.png`. The training script has been updated to save one on the next rerun, but that image still needs to be generated from a real run before submission if the validator enforces a strict loss-curve requirement.

## Kaggle Note

If an older public Kaggle notebook still exists, it does **not** need to be deleted as long as your README points judges to the current source-of-truth assets in this repo. If you want to reduce confusion, rename the older notebook as an archived draft instead of removing it.

---

## API Quick Start

```python
import requests
import uuid

BASE = "https://abhishekkharat11-ai-tribunal-env.hf.space"
session_id = f"demo-{uuid.uuid4()}"

reset = requests.post(
    f"{BASE}/reset",
    json={"task_level": 2, "session_id": session_id},
).json()
obs = reset["observation"]
episode_id = obs["episode_id"]

result = requests.post(
    f"{BASE}/step",
    json={
        "session_id": session_id,
        "episode_id": episode_id,
        "task_level": 2,
        "action": {
            "action_type": "examine_evidence",
            "reasoning": "I will examine evidence E3 because its timing and metadata are suspicious.",
            "target": "E3",
            "evidence_reliability_assessments": {"E3": 0.2}
        }
    }
).json()

print(result["observation"]["step_score"])
```

For the browser demo, use the custom game UI at `/` which manages a session automatically through `/game/reset` and `/game/step`.

---

## Agent Access

The Space exposes a lightweight agent wrapper at [`/agents.md`](https://abhishekkharat11-ai-tribunal-env.hf.space/agents.md).

- Use `/game/reset` + `/game/step` for the simplest tool-style integration.
- Use `/reset` + `/step` if you want the standard OpenEnv HTTP contract.
- Reuse the same `session_id` across related cases when you want precedent consistency to carry forward.

The Hugging Face header-level Agents button is not required for this submission because this project is a Docker Space, not a Gradio Space with native agent header integration.

---

## API Endpoints

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
| `/game/cojudge` | POST | Ask the optional HF Router-backed AI Co-Judge for the next best move |
| `/agents.md` | GET | Plain-text wrapper for external coding agents and tool discovery |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |

---

*Built for the Meta PyTorch OpenEnv Hackathon by Abhishek Kharat.*
