"""FastAPI app for containerized execution (HF Space compatible)."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from env import Action, SupportEnv, TASKS, TICKETS, grade

app = FastAPI(title="support-ticket-env", version="0.1.0")


class RunTaskRequest(BaseModel):
    task_id: str = Field(..., description="One of: easy, medium, hard")
    action: Action


@app.get("/")
def root() -> dict:
    return {
        "name": "support-ticket-env",
        "status": "ok",
        "tasks": list(TASKS.keys()),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.post("/run-task")
def run_task(req: RunTaskRequest) -> dict:
    if req.task_id not in TASKS:
        return {"error": f"Unknown task_id '{req.task_id}'. Use one of {list(TASKS.keys())}"}

    task = TASKS[req.task_id]
    expected = TICKETS[task.ticket_index]

    env = SupportEnv()
    obs = env.reset(task_id=req.task_id)
    next_obs, env_reward, done, info = env.step(req.action)
    grader_score = grade(req.task_id, req.action, expected)

    return {
        "task_id": req.task_id,
        "ticket_id": obs.ticket_id,
        "observation": next_obs.model_dump(),
        "env_reward": env_reward.model_dump(),
        "grader_score": grader_score,
        "done": done,
        "info": info,
    }
