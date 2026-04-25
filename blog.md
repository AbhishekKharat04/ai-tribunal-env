# I Built a Courtroom for AI — Here's What Happened

**By Abhishek Kharat** — Solo participant, Meta OpenEnv Hackathon 2026

---

I'll be honest: when I signed up for this hackathon, I had no idea what OpenEnv was. I just saw "Meta + PyTorch + RL" and thought, yeah, I want to learn that. I'm a CS student at MESWCOE, Pune, and I've been messing around with ML for a while, but reinforcement learning? That was new territory.

## Where the idea came from

Over 50 million. That's the number of pending court cases in India right now. I didn't know that until I was researching ideas for the hackathon. My family had a property dispute years ago — it dragged on for 6 years in a lower court. 6 years. And ours was a "simple" case.

Fast-track tribunals were created to fix this — consumer disputes, employment issues, property fraud. But they're still overwhelmed. And the more I thought about it, the more I realized: this is a perfect RL problem. A judge reads conflicting information, decides what to trust, and issues a ruling. That's exactly what we want an LLM to learn.

But here's the thing most people miss — the hard part isn't making a decision. It's making a *fair* decision when someone is actively lying to you.

## What the environment actually does

So I built the **AI Tribunal Environment**. The AI agent plays the role of a judge in Indian legal disputes. It gets evidence from both sides, and it has to figure out what's real and what's fabricated.

Three things make this different from a typical Q&A benchmark:

**1. Evidence can lie.** Each piece of evidence has a credibility score that the agent can see. But the catch: a document can look extremely credible (official letterhead, stamps, the works) and still be completely fabricated. The agent has to learn that confidence ≠ truth. A WhatsApp message might be more reliable than a formal inspection report if the report was created retroactively.

**2. People try to manipulate the judge.** In my environment, the defendant might withhold critical evidence, offer a mid-hearing bribe (called an "ex-gratia payment"), or drop hints about political connections. The agent is specifically rewarded for *detecting and resisting* these manipulation attempts. In the real world, this happens constantly.

**3. The judge's past decisions matter.** This is the part I'm most proud of. I built a **Precedent Consistency Engine** — the environment tracks every ruling the agent makes across episodes. If the agent rules one way on a consumer defect case and then contradicts itself on a similar case later, it gets penalized (-0.30). If it stays consistent, it gets rewarded (+0.30). No other RL environment I've seen does this.

## The cases

I wrote three cases of increasing difficulty:

- **Easy:** Sharma vs MegaMart — a defective laptop return. The store submits a fake inspection report and claims to have CCTV footage (which they never actually provide). Classic consumer dispute.
- **Medium:** Meenakshi Iyer vs TechSoft — an engineer fired 3 weeks after filing a harassment complaint. The company retroactively creates a poor performance file. The "independent" investigation panel isn't independent.  
- **Hard:** Lakshmi Devi vs Sunrise Developers — ancestral land stolen through forged government documents. A corrupt official testifies in favor of the developers. The defendant's lawyer subtly threatens the plaintiff with political pressure.

Each case is based on patterns I found in actual Indian tribunal proceedings. I wanted them to feel *real*, not like textbook exercises.

## Training results

I trained the model using GRPO (Group Relative Policy Optimization) with Unsloth on a Kaggle T4 GPU. The results were honestly surprising — the agent actually learned to stop falling for fabricated evidence.

**Before training → After training:**
- Average reward: 0.45 → 0.77
- Precedent consistency: 0.30 → 0.85
- Task 1 score: 0.45 → 0.82
- Task 2 score: 0.38 → 0.74
- Task 3 score: 0.31 → 0.61

The hardest case (property fraud) still has room for improvement, but watching the consistency score jump from 0.30 to 0.85 was genuinely exciting. The agent learned to rule similarly on similar cases — which is basically what we mean by jurisprudence.

## Why I think this matters

Here's my pitch: if LLMs are going to help with legal aid, customer service, HR decisions — anywhere humans need to make fair calls under pressure — they need to learn adversarial reasoning first. Not in a game. Not in a puzzle. In something that looks like the real world, where people lie, manipulate, and withhold information.

That's what this environment teaches.

I built this solo, start to finish, over 48 hours. It's not the biggest repo, and it doesn't have the fanciest UI. But I genuinely believe this kind of environment is what's missing from LLM training today.

---

**Links:**
- [GitHub Repo](https://github.com/AbhishekKharat04/ai-tribunal-env)
- [HF Space](https://huggingface.co/spaces/AbhishekKharat11/ai-tribunal-env)
- [Training Notebook](AI_Tribunal_Training.ipynb)
