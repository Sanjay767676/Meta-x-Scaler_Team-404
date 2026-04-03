"""OpenAI baseline runner with structured submission logs.

Required env vars (api mode): API_BASE_URL, MODEL_NAME, HF_TOKEN
"""

from __future__ import annotations

import os
import json
import time
from typing import Any, Optional

from openai import OpenAI

from env import Action, SupportEnv, TASKS, TICKETS, grade


def _emit(tag: str, **fields: Any) -> None:
    """Emit machine-parseable logs in required [TAG] format."""
    payload = " ".join(f"{k}={json.dumps(v, ensure_ascii=True)}" for k, v in fields.items())
    print(f"[{tag}] {payload}")


def parse_model_output(raw: str) -> Action:
    """Parse model text output into a typed Action with safe defaults."""
    fields: dict[str, str] = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()

    return Action(
        category=fields.get("category", "unknown"),
        priority=fields.get("priority", "medium"),
        action=fields.get("action", "guide"),
        response=fields.get("response", ""),
        resolve=fields.get("resolve", "false").lower() == "true",
    )


def build_prompt(task_id: str, user_query: str, history: list[str]) -> str:
    """Build a deterministic task-specific prompt for the model."""
    task = TASKS[task_id]
    return (
        "You are a customer support triage agent.\n"
        f"Task difficulty: {task.difficulty}\n"
        f"Task objective: {task.objective}\n"
        "Return ONLY the following keys, one per line:\n"
        "category: <billing|account|technical>\n"
        "priority: <low|medium|high>\n"
        "action: <refund|escalate|guide>\n"
        "response: <short customer-facing response>\n"
        "resolve: <true|false>\n\n"
        f"User query: {user_query}\n"
        f"Conversation history: {history}\n"
    )


def call_model(client: OpenAI, prompt: str, model: str) -> str:
    """Call OpenAI Chat Completions with deterministic settings."""
    seed_raw = os.getenv("OPENAI_SEED", "7")
    seed = int(seed_raw)
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        top_p=1,
        seed=seed,
        messages=[
            {"role": "system", "content": "Follow the requested output format exactly."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content or ""


def mock_model_output(expected: dict, step: int) -> str:
    """Deterministic fallback output for local testing without API access."""
    resolve_value = "true" if step >= 2 else "false"
    if expected["action"] == "refund":
        response = "We identified the duplicate charge and will process a refund to your original payment method."
    elif expected["action"] == "escalate":
        response = "We escalated this to a specialist team for urgent investigation and updates."
    else:
        response = "Please follow these steps in settings to complete the requested change."

    return (
        f"category: {expected['category']}\n"
        f"priority: {expected['priority']}\n"
        f"action: {expected['action']}\n"
        f"response: {response}\n"
        f"resolve: {resolve_value}"
    )


def run_task(task_id: str, client: Optional[OpenAI], model: str, mode: str) -> dict[str, Any]:
    """Run one task and return reproducible grader and environment scores."""
    task = TASKS[task_id]
    expected = TICKETS[task.ticket_index]

    env = SupportEnv()
    obs = env.reset(task_id=task_id)
    done = False
    episode_return = 0.0
    info: dict[str, Any] = {"step": 0}
    action = Action(
        category="unknown",
        priority="medium",
        action="guide",
        response="",
        resolve=False,
    )

    while not done:
        prompt = build_prompt(task_id=task_id, user_query=obs.user_query, history=obs.conversation_history)
        if mode == "mock":
            raw_output = mock_model_output(expected=expected, step=info["step"] + 1)
        else:
            if client is None:
                raise RuntimeError("OpenAI client is required in api mode.")
            raw_output = call_model(client=client, prompt=prompt, model=model)
        action = parse_model_output(raw_output)
        obs, env_reward, done, info = env.step(action)
        episode_return += env_reward.score
        _emit(
            "STEP",
            task=task_id,
            step=info["step"],
            ticket_id=info["ticket_id"],
            done=done,
            env_reward=env_reward.score,
        )

    grader_score = grade(task_id, action, expected)

    return {
        "task": task_id,
        "ticket_id": obs.ticket_id,
        "done": done,
        "step": info["step"],
        "grader_score": grader_score,
        "episode_return": round(episode_return, 4),
        "action": action,
    }


def run_baseline() -> None:
    """Run all tasks (easy, medium, hard) and print baseline summary."""
    mode = os.getenv("BASELINE_MODE", "api").lower().strip()
    api_base_url = os.getenv("API_BASE_URL", "").strip()
    model = os.getenv("MODEL_NAME", "").strip()
    api_key = os.getenv("HF_TOKEN", "").strip()

    if mode != "mock":
        missing = [
            name
            for name, value in (
                ("API_BASE_URL", api_base_url),
                ("MODEL_NAME", model),
                ("HF_TOKEN", api_key),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required env vars in api mode: {', '.join(missing)}")
    else:
        if not api_base_url:
            api_base_url = "mock://local"
        if not model:
            model = "gpt-4o-mini"

    seed = int(os.getenv("OPENAI_SEED", "7"))
    output_path = os.getenv("BASELINE_OUTPUT", "baseline_scores.json")
    max_runtime_seconds = int(os.getenv("MAX_RUNTIME_SECONDS", "1100"))
    start = time.monotonic()

    client = OpenAI(api_key=api_key, base_url=api_base_url) if mode != "mock" else None

    task_order = ["easy", "medium", "hard"]
    _emit(
        "START",
        mode=mode,
        model=model,
        api_base_url=api_base_url,
        max_runtime_seconds=max_runtime_seconds,
        tasks=task_order,
        seed=seed,
    )

    results = [run_task(task_id=t, client=client, model=model, mode=mode) for t in task_order]

    print(f"[BASELINE] mode={mode} | model={model} | seed={seed}")
    total = 0.0
    for r in results:
        total += r["grader_score"]
        a = r["action"]
        print(
            f"[TASK {r['task'].upper()}] ticket_id={r['ticket_id']} | "
            f"grader_score={r['grader_score']:.4f} | episode_return={r['episode_return']:.4f} | steps={r['step']}"
        )
        print(
            f"             category={a.category} | priority={a.priority} | "
            f"action={a.action} | resolve={a.resolve}"
        )

    avg = total / len(results)
    print(f"[SUMMARY] average_grader_score={avg:.4f}")

    payload = {
        "model": model,
        "seed": seed,
        "scores": [
            {
                "task": r["task"],
                "ticket_id": r["ticket_id"],
                "grader_score": r["grader_score"],
                "episode_return": r["episode_return"],
                "steps": r["step"],
            }
            for r in results
        ],
        "average_grader_score": round(avg, 4),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[ARTIFACT] wrote {output_path}")

    elapsed = round(time.monotonic() - start, 3)
    if elapsed > max_runtime_seconds:
        raise TimeoutError(
            f"Inference runtime exceeded MAX_RUNTIME_SECONDS ({elapsed}s > {max_runtime_seconds}s)."
        )
    _emit(
        "END",
        average_grader_score=round(avg, 4),
        runtime_seconds=elapsed,
        output_path=output_path,
        tasks=len(results),
    )


if __name__ == "__main__":
    run_baseline()
