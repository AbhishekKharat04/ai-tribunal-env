# AGENTS.md

## Production Surface

This repository exposes two user-facing ways to interact with the environment:

1. Standard OpenEnv HTTP API
   - `POST /reset`
   - `POST /step`
   - `GET /state`
   - Use the returned `session_id` and `episode_id` fields to continue a stateless HTTP episode.

2. Session-aware game API
   - `POST /game/reset`
   - `POST /game/step`
   - Use this flow for browser demos, agent wrappers, and evaluation loops that need a simpler stateful contract.

## Core Files

- `server/tribunal_environment.py`: environment state, scoring flow, session-scoped precedent handling
- `server/app.py`: FastAPI routes, baseline helper, `/agents.md` wrapper
- `server/grader.py`: reward logic
- `server/precedent_engine.py`: precedent matching and consistency scoring
- `models.py`: OpenEnv action/observation models
- `train_tribunal_grpo.py`: training client and evaluation loop
- `inference.py`: simple benchmark runner against the live Space

## Agent Notes

- Prefer `/game/reset` + `/game/step` for simple tool use.
- Prefer `/reset` + `/step` only when you explicitly want OpenEnv-native behavior.
- Start a new logical run with a new `session_id`.
- Reuse the same `session_id` across related cases when you want precedent consistency to carry forward.
