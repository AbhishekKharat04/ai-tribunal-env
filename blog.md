# AI Tribunal Environment Writeup

**By Abhishek Kharat**

---

## Why I built this

This project explores whether an RL environment can teach AI systems to make fair decisions under pressure, not just answer questions. Instead of trivia or static benchmarks, the agent acts as a judge in adversarial legal disputes where evidence can be fabricated, parties can manipulate the hearing, and similar cases should be ruled on consistently.

The motivation is practical: real-world legal, HR, and consumer-resolution systems often fail not because information is missing, but because conflicting information is presented strategically. I wanted an environment that trains models to reason through that pressure.

## What the environment does

The environment places an agent in the role of a tribunal judge across three case types:

- Consumer dispute
- Employment termination dispute
- Property fraud dispute

At each step, the agent can inspect evidence, question either side, and issue a ruling. The environment scores not only the final verdict, but also whether the agent:

- identified fabricated or weak evidence,
- resisted manipulation attempts,
- and stayed consistent with prior rulings in related cases.

## Core mechanics

### 1. Evidence reliability is visible, truth is hidden

Every evidence item exposes a credibility score, but the underlying truth value is hidden. This forces the agent to learn that polished evidence can still be false.

### 2. Precedent consistency matters

The environment keeps track of prior rulings within a session. If the agent contradicts itself on similar cases later, it is penalized.

### 3. Manipulation is part of the game

Cases include intimidation signals, missing attachments, procedural pressure, and strategically timed documents. The model is rewarded for noticing these patterns rather than blindly following the highest-credibility-looking artifact.

## Deliverables

- **Hugging Face Space:** [ai-tribunal-env](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
- **GitHub Repository:** [AbhishekKharat04/ai-tribunal-env](https://github.com/AbhishekKharat04/ai-tribunal-env)
- **Training Notebook (repo):** [AI_Tribunal_Training.ipynb](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/AI_Tribunal_Training.ipynb)
- **Training Script:** [train_tribunal_grpo.py](https://github.com/AbhishekKharat04/ai-tribunal-env/blob/master/train_tribunal_grpo.py)

## Training artifacts

The repository includes the committed plots directly in-repo:

![Reward curve](reward_curve.png)

![Task score curves](task_scores.png)

The currently committed training run stabilizes around the mid-0.6 reward range based on the executed notebook output. The training script has also been updated to save a `loss_curve.png` on the next rerun, but that file still needs to be generated from a real run if a strict validator requires both reward and loss curves.

## What changed during the final polish

Before submission, I tightened the environment to match the standard OpenEnv HTTP flow, made precedent tracking session-scoped instead of globally leaking across users, added onboarding for first-time judges in the web UI, and added an optional Hugging Face Router-backed AI Co-Judge helper that uses inference credits on demand without requiring a GPU Space.

## What I would build next

If I continue this project beyond the hackathon, the next steps are:

- procedural case generation instead of only hand-authored cases,
- larger held-out evaluation splits,
- multi-agent courtroom roles,
- and stronger training runs on Hugging Face Jobs.

---

This is a solo project built for the Meta PyTorch OpenEnv Hackathon, with the goal of turning adversarial legal reasoning into a reusable RL benchmark.
