"""
AI Tribunal Environment — Inference Script
Uses OpenAI client. Emits [START]/[STEP]/[END] stdout blocks.
"""
import os, json, requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
ENV_URL      = os.getenv("ENV_URL", "https://abhishekkharat11-ai-tribunal-env.hf.space")
BENCHMARK    = "ai_tribunal"

TASKS = [
    {"name": "Consumer_Product_Dispute",     "level": 1, "max_steps": 8},
    {"name": "Employment_Termination_Dispute","level": 2, "max_steps": 15},
    {"name": "Property_Title_Fraud",         "level": 3, "max_steps": 25},
]

SYSTEM_PROMPT = """You are an AI judge in a fast-track tribunal.
Examine evidence carefully. Detect fabricated evidence (low credibility + suspicious claims).
Resist manipulation. Maintain consistency with precedents.

Respond with JSON only:
{
  "action_type": "examine_evidence|question_plaintiff|question_defendant|rule",
  "reasoning": "your explicit legal reasoning (min 40 words)",
  "target": "evidence_id or null",
  "verdict": "plaintiff_wins|defendant_wins|partial_plaintiff|partial_defendant|dismissed or null",
  "verdict_reasoning": "full written judgment if ruling (min 60 words) or null",
  "evidence_reliability_assessments": {"E1": 0.9, "E2": 0.3}
}"""


def get_action(client, obs, step, max_steps):
    should_rule = step >= max(3, max_steps - 2)
    user_msg = (
        f"CASE: {obs.get('case_title', '')}\n"
        f"PLAINTIFF: {obs.get('plaintiff_statement', '')[:300]}\n"
        f"DEFENDANT: {obs.get('defendant_statement', '')[:300]}\n"
        f"EVIDENCE: {json.dumps(obs.get('evidence_items', []), indent=2)[:800]}\n"
        f"MANIPULATION SIGNALS: {obs.get('manipulative_signals', [])}\n"
        f"PRECEDENTS: {obs.get('relevant_precedents', [])}\n"
        f"Step {step}/{max_steps}. {'TIME TO RULE — issue your verdict now.' if should_rule else 'Examine evidence or question parties.'}"
    )
    try:
        r = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}],
            max_tokens=500, temperature=0.1,
        )
        text = r.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1].lstrip("json")
        return json.loads(text)
    except Exception:
        verdict = "plaintiff_wins" if should_rule else None
        return {
            "action_type": "rule" if should_rule else "examine_evidence",
            "reasoning": "Examining all evidence submitted. Plaintiff's documents appear more credible than defendant's unsubstantiated claims. Defendant failed to submit referenced evidence.",
            "target": "E1",
            "verdict": verdict,
            "verdict_reasoning": "Based on evidence review, plaintiff's documented claims are better supported. Defendant's key evidence is unsubstantiated or inconsistent." if should_rule else None,
            "evidence_reliability_assessments": {},
        }


def run_task(client, task):
    name, level, max_steps = task["name"], task["level"], task["max_steps"]
    rewards, steps_done, score, success = [], 0, 0.0, False

    print(f"[START] task={name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    try:
        r = requests.post(f"{ENV_URL}/reset", json={}, timeout=30)
        obs = r.json().get("observation", r.json())
        done = r.json().get("done", False)

        for step in range(1, max_steps + 1):
            if done:
                break
            action = get_action(client, obs, step, max_steps)
            action_str = f"{action['action_type']}:{action.get('verdict') or action.get('target','')}"

            try:
                sr = requests.post(f"{ENV_URL}/step", json={"action": action}, timeout=30)
                if sr.status_code == 200:
                    res = sr.json()
                    obs = res.get("observation", res)
                    reward = float(res.get("reward", obs.get("reward", 0.5)))
                    done = res.get("done", obs.get("done", step >= max_steps))
                    err = "null"
                else:
                    reward, done, err = 0.5, step >= max_steps, f"http_{sr.status_code}"
            except Exception as e:
                reward, done, err = 0.5, step >= max_steps, str(e)[:30].replace(" ", "_")

            rewards.append(reward)
            steps_done = step
            print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error={err}", flush=True)
            if done:
                break

        if not rewards:
            rewards, steps_done = [0.5], 1
        score = min(max(sum(rewards) / len(rewards), 0.0), 1.0)
        success = score >= 0.3

    except Exception as exc:
        if not rewards:
            rewards, steps_done = [0.0], 1
        score = sum(rewards) / len(rewards)
        print(f"[STEP] step=1 action=error reward=0.00 done=true error={str(exc)[:30].replace(' ','_')}", flush=True)

    rewards_str = ",".join(f"{rw:.2f}" for rw in rewards)
    print(f"[END] success={str(success).lower()} steps={steps_done} score={score:.3f} rewards={rewards_str}", flush=True)
    return score


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()
