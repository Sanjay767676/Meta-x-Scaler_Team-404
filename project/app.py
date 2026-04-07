"""FastAPI app for containerized execution (HF Space compatible)."""

from __future__ import annotations

from fastapi import FastAPI, Body
from fastapi import HTTPException
from pydantic import BaseModel, Field

from env import Action, SupportEnv, TASKS, TICKETS, grade

app = FastAPI(title="support-ticket-env", version="0.1.0")
RUNTIME_ENV = SupportEnv()


class RunTaskRequest(BaseModel):
    task_id: str = Field(..., description="One of: easy, medium, hard")
    action: Action


class ResetRequest(BaseModel):
    task_id: str | None = Field(default=None, description="Optional task id: easy, medium, hard")
    ticket_index: int = Field(default=0, description="Fallback dataset index when task_id is omitted")


class StepRequest(BaseModel):
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


@app.post("/reset")
def reset(req: ResetRequest = Body(default=ResetRequest())) -> dict:
    try:
        obs = RUNTIME_ENV.reset(ticket_index=req.ticket_index, task_id=req.task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"observation": obs.model_dump(), "state": RUNTIME_ENV.state()}


@app.post("/step")
def step(req: StepRequest = Body(...)) -> dict:
    try:
        obs, reward, done, info = RUNTIME_ENV.step(req.action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
        "state": RUNTIME_ENV.state(),
    }


@app.get("/state")
def state() -> dict:
    return RUNTIME_ENV.state()


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
