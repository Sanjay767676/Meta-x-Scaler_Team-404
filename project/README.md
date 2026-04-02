# Support Ticket Environment

An OpenEnv-compatible reinforcement learning environment for training and
evaluating agents on customer support ticket resolution tasks.

## Project structure

```
project/
├── env/
│   ├── __init__.py     # Public API re-exports
│   ├── models.py       # Pydantic models (Ticket, Observation, Action, …)
│   ├── env.py          # SupportTicketEnv — OpenEnv-compatible class
│   ├── tasks.py        # Task definitions and sample task catalogue
│   └── graders.py      # Episode grading functions
├── openenv.yaml        # OpenEnv manifest
├── inference.py        # Example agent loop
├── Dockerfile          # Container definition (Python 3.10)
└── requirements.txt    # Python dependencies
```

## Requirements

- Python 3.10
- [pydantic](https://docs.pydantic.dev/) >= 2.0

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick start

```python
from env import SupportTicketEnv, Action, SAMPLE_TASKS
from env.graders import composite_grader

task = SAMPLE_TASKS[0]
env = SupportTicketEnv(max_steps=task.max_steps)

obs = env.reset(ticket=task.ticket)
results = []
done = False

while not done:
    action = Action(action_type="no_op")  # replace with your policy
    result = env.step(action)
    results.append(result)
    done = result.done

score = composite_grader(results)
print(f"Score: {score:.4f}")
```

Or run the bundled example:

```bash
python inference.py
```

## Docker

```bash
docker build -t support-ticket-env .
docker run --rm support-ticket-env
```

## Extending the environment

| What to extend | Where |
|---|---|
| Add new data models | `env/models.py` |
| Implement action dispatch logic | `env/env.py` → `step()` |
| Add more task scenarios | `env/tasks.py` → `SAMPLE_TASKS` |
| Add or tune graders | `env/graders.py` |
| Swap in a real agent policy | `inference.py` |
