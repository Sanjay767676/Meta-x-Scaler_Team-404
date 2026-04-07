---
title: support-ticket-env
sdk: docker
tags:
	- openenv
	- reinforcement-learning
	- customer-support
---

# Support Ticket OpenEnv Environment

This project is a real-world customer support simulation environment for agent
training and evaluation. Agents must triage and respond to support tickets with
correct category, priority, and next action.

## Why this environment

Support triage is a practical business workflow (billing/account/technical) and
is useful for benchmarking planning, classification, and response quality in
agent systems.

The dataset includes diverse operational scenarios such as duplicate charges,
SSO failures, webhook outages, VAT invoice requests, permission cleanup, and
subscription changes.

## OpenEnv compatibility

This repo includes:

- Typed Pydantic models for observation/action/reward in [env/models.py](env/models.py)
- Environment API in [env/env.py](env/env.py): `reset(task_id=...)`, `step()`, `state()`
- Manifest in [openenv.yaml](openenv.yaml)
- Task catalog in [env/tasks.py](env/tasks.py)
- Deterministic graders in [env/graders.py](env/graders.py)

## Action and observation spaces

Observation (`Observation`):

- `ticket_id: str`
- `user_query: str`
- `category: Optional[str]`
- `priority: Optional[str]`
- `conversation_history: list[str]`

Action (`Action`):

- `category: str` (`billing | account | technical`)
- `priority: str` (`low | medium | high`)
- `action: str` (`refund | escalate | guide`)
- `response: str`
- `resolve: bool`

Reward (`Reward`):

- `score: float` in `[0.0, 1.0]`
- `reason: Optional[str]`

## Tasks and difficulty progression

Defined in [env/tasks.py](env/tasks.py):

- `easy`: category-only classification task
- `medium`: category + priority classification
- `hard`: full resolution (category + priority + action + response quality)

Hard mode is intentionally multi-step: agents should diagnose first, then
resolve after enough confidence. Premature resolution is penalized.

Each task has deterministic grading in [env/graders.py](env/graders.py) with
scores in `[0.0, 1.0]`.

## Reward design

Main trajectory reward (see [env/env.py](env/env.py)):

- `+0.3` category correct
- `+0.2` priority correct
- `+0.3` action correct
- `+0.2` response keyword match
- `-0.25` premature resolve penalty in hard mode
- `-0.2` penalty if category, priority, and action are all wrong

This provides dense partial-progress signal, not only terminal binary reward.

## Setup

Requirements:

- Python 3.10+

Install:

```bash
pip install -r requirements.txt
```

## Baseline inference (OpenAI API)

[inference.py](inference.py) runs a baseline model on all 3 tasks and prints
per-task scores plus average score.

Set environment variables:

```bash
set OPENAI_API_KEY=your_key_here
set OPENAI_MODEL=gpt-4o-mini
```

Run baseline:

```bash
python inference.py
```

Output includes:

- Task score for `easy`, `medium`, `hard`
- Episode return and grader score
- Summary average grader score

The script also writes a machine-readable artifact (`baseline_scores.json`) for
submission evidence.

## Baseline scores

Latest local run (deterministic mock mode) from `baseline_scores.json`:

| Task | Grader Score | Episode Return | Steps |
|---|---:|---:|---:|
| easy | 1.0000 | 1.9000 | 2 |
| medium | 1.0000 | 1.9000 | 2 |
| hard | 1.0000 | 1.9000 | 2 |
| **Average** | **1.0000** | - | - |

Note: these values were generated with `BASELINE_MODE=mock` because
`OPENAI_API_KEY` was unavailable in this environment. For official submission,
rerun with API mode and replace the table with real model scores.

## Docker

Build and run:

```bash
docker build -t support-ticket-env .
docker run --rm -p 7860:7860 support-ticket-env
```

Health check:

```bash
curl http://localhost:7860/health
```

## Hugging Face Spaces deployment

Use Docker Space mode:

1. Create a new Hugging Face Space (SDK: Docker).
2. Push this `project/` directory content to the Space repository.
3. Add Space tag `openenv` in Space settings.
4. Start the Space and verify `/health` returns `{"status": "healthy"}`.

Container entrypoint is configured in [Dockerfile](Dockerfile) with:

- `uvicorn app:app --host 0.0.0.0 --port 7860`

## Validation checklist

- `python inference.py` runs end-to-end baseline
- `docker build` and `docker run` succeed
- `openenv.yaml` present and configured
- task graders deterministic and bounded `[0.0, 1.0]`

## Submission evidence (captured)

### OpenEnv validation

Command:

```bash
openenv validate
```

Output:

```text
[OK] project: Ready for multi-mode deployment
```

### Baseline artifact generation

Command used in this environment:

```bash
BASELINE_MODE=mock python inference.py
```

Output summary:

```text
[BASELINE] mode=mock | model=gpt-4o-mini | seed=7
[TASK EASY] ticket_id=3 | grader_score=1.0000 | episode_return=1.9000 | steps=2
[TASK MEDIUM] ticket_id=2 | grader_score=1.0000 | episode_return=1.9000 | steps=2
[TASK HARD] ticket_id=13 | grader_score=1.0000 | episode_return=1.9000 | steps=2
[SUMMARY] average_grader_score=1.0000
[ARTIFACT] wrote baseline_scores.json
```

### Local API health proof

Command:

```bash
python -c "from fastapi.testclient import TestClient; from app import app; c=TestClient(app); r=c.get('/health'); print(r.status_code, r.json())"
```

Output:

```text
200 {'status': 'healthy'}
```

### Docker status in this environment

Build command:

```bash
docker build -t support-ticket-env-proof .
```

Build output:

```text
[+] Building ... FINISHED
=> naming to docker.io/library/support-ticket-env-proof:latest
```

Run command:

```bash
docker run --rm -p 7860:7860 support-ticket-env-proof
```

Runtime health proof:

```text
GET  http://127.0.0.1:7860/health  -> 200 {"status":"healthy"}
POST http://127.0.0.1:7860/reset   -> 200 {"observation":..., "state":...}
```

### Hugging Face Space live health response

Live deployment proof:

```text
GET  https://sanjay7676-meta-x-scaler.hf.space/health -> 200 {"status":"healthy"}
POST https://sanjay7676-meta-x-scaler.hf.space/reset  -> 200 {"observation":..., "state":...}
```

## Project structure

```text
project/
├── app.py              # FastAPI app for container/HF runtime
├── env/
│   ├── __init__.py
│   ├── dataset.py
│   ├── env.py
│   ├── graders.py
│   ├── models.py
│   └── tasks.py
├── openenv.yaml
├── inference.py        # OpenAI baseline runner (easy/medium/hard)
├── Dockerfile
└── requirements.txt
```
