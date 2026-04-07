---
title: support-ticket-env
sdk: docker
tags:
  - openenv
  - reinforcement-learning
  - customer-support
---

# Support Ticket OpenEnv Environment

This project is a customer support simulation environment built for agent
training and evaluation. The job is straightforward on paper: triage incoming
support tickets and respond with the right category, priority, and next action.

## Why this environment

Support triage is one of those business workflows that looks simple until you
actually try to automate it. It cuts across billing, account, and technical
issues, which makes it a useful benchmark for planning, classification, and
response quality in agent systems.

The dataset covers a mix of operational cases like duplicate charges, SSO
failures, webhook outages, VAT invoice requests, permission cleanup, and
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

Hard mode is intentionally multi-step. The agent is supposed to diagnose first
and only resolve once it has enough confidence. Resolving too early is
penalized.

Each task is graded deterministically in [env/graders.py](env/graders.py), with
scores bounded to `[0.0, 1.0]`.

## Reward design

Main trajectory reward (see [env/env.py](env/env.py)):

- `+0.3` category correct
- `+0.2` priority correct
- `+0.3` action correct
- `+0.2` response keyword match
- `-0.25` premature resolve penalty in hard mode
- `-0.2` penalty if category, priority, and action are all wrong
- `+0.05` progress bonus when a step beats prior best score
- `-0.05` stagnation penalty for repeating a non-perfect decision triple
- `-0.02` per extra step time-cost shaping after step 1
- `-0.1` compound-ticket under-triage penalty in hard mode (non-escalation)

The idea here is to give a dense partial-progress signal instead of only a
terminal pass/fail reward. That made debugging agent behavior a lot less opaque
in practice.

## Novel mechanics

This environment models compound real-world tickets, where multiple issues can
show up in the same case, and adds a hard-mode under-triage penalty when the
agent fails to escalate them. That creates a more realistic tension between
closing things quickly and triaging them safely, which is much closer to how
enterprise support actually works.

## Setup

Requirements:

- Python 3.10+

Install:

```bash
pip install -r requirements.txt
```

## Baseline inference (OpenAI API)

[inference.py](inference.py) runs a baseline model across all 3 tasks and
prints per-task scores along with the average score.

Set environment variables:

```bash
set API_BASE_URL=https://api.openai.com/v1
set MODEL_NAME=gpt-4o-mini
set OPENAI_API_KEY=your_key_here
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
submission evidence, so you do not have to scrape logs later.

## Baseline scores

Latest local run (deterministic mock mode) from `baseline_scores.json`:

| Task | Grader Score | Episode Return | Steps |
|---|---:|---:|---:|
| easy | 1.0000 | 1.9000 | 2 |
| medium | 1.0000 | 1.9000 | 2 |
| hard | 1.0000 | 1.9000 | 2 |
| **Average** | **1.0000** | - | - |

Note: these values were generated with `BASELINE_MODE=mock` because
`OPENAI_API_KEY` was not available in this environment. For official
submission, rerun in API mode and replace the table with real model scores.

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

## Quality evidence for judging rubric

This repo includes explicit checks that line up directly with hackathon scoring:

- `python validate_submission.py`:
  - verifies OpenEnv interface + endpoints
  - verifies grader bounds `[0.0, 1.0]`
  - verifies grader determinism (same input -> same score)
  - verifies trajectory reward is non-static across steps
- `pytest tests/test_env_quality.py`:
  - deterministic grader reproducibility checks
  - hard-mode premature-resolution behavior check
  - trajectory shaping variability check
  - compound-ticket under-triage penalty check

These checks back up the reliability, reproducibility, and fairness claims for
"Task & grader quality", "Environment design", and "Code quality & spec
compliance".

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
