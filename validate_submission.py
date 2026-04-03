"""Local pre-submission validator for the support-ticket OpenEnv project."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from env import Action, SupportEnv, TASKS, TICKETS, grade


def _ok(msg: str) -> None:
    print(f"[PASS] {msg}")


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def check_files() -> None:
    for file_name in ("inference.py", "openenv.yaml", "Dockerfile"):
        if not Path(file_name).exists():
            _fail(f"Missing required file: {file_name}")
    _ok("Required root files exist (inference.py, openenv.yaml, Dockerfile)")


def check_openenv_spec() -> None:
    text = Path("openenv.yaml").read_text(encoding="utf-8")
    required_tokens = ("entry_point:", "module: env", "class: SupportEnv", "tasks:", "tasks_module:", "graders_module:")
    for token in required_tokens:
        if token not in text:
            _fail(f"openenv.yaml missing token: {token}")

    env = SupportEnv()
    if not hasattr(env, "reset") or not hasattr(env, "step") or not hasattr(env, "state"):
        _fail("SupportEnv must expose reset(), step(), and state()")
    _ok("OpenEnv manifest and env interface look compliant")


def check_api_endpoints() -> None:
    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200:
        _fail(f"/health expected 200, got {health.status_code}")

    reset_resp = client.post("/reset", json={"task_id": "easy"})
    if reset_resp.status_code != 200:
        _fail(f"/reset expected 200, got {reset_resp.status_code}")

    step_resp = client.post(
        "/step",
        json={
            "action": {
                "category": "technical",
                "priority": "low",
                "action": "guide",
                "response": "Please follow these steps in settings.",
                "resolve": True,
            }
        },
    )
    if step_resp.status_code != 200:
        _fail(f"/step expected 200, got {step_resp.status_code}")
    _ok("HTTP endpoints /health, /reset, /step respond correctly")


def check_tasks_and_graders() -> None:
    if len(TASKS) < 3:
        _fail("Need at least 3 tasks")

    for task_id, task in TASKS.items():
        expected = TICKETS[task.ticket_index]
        best_action = Action(
            category=expected["category"],
            priority=expected["priority"],
            action=expected["action"],
            response="We escalated this issue and will share updates.",
            resolve=True,
        )
        low_action = Action(
            category="unknown",
            priority="unknown",
            action="unknown",
            response="",
            resolve=False,
        )
        for label, action in (("best", best_action), ("low", low_action)):
            score = grade(task_id, action, expected)
            if not (0.0 <= score <= 1.0):
                _fail(f"Task {task_id} grader out of range for {label} action: {score}")
    _ok("Tasks >= 3 and grader outputs are bounded to [0.0, 1.0]")


def check_inference_mock() -> None:
    env = os.environ.copy()
    env["BASELINE_MODE"] = "mock"
    env["API_BASE_URL"] = env.get("API_BASE_URL", "mock://local")
    env["MODEL_NAME"] = env.get("MODEL_NAME", "gpt-4o-mini")
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY", "mock-token")
    env["MAX_RUNTIME_SECONDS"] = env.get("MAX_RUNTIME_SECONDS", "1100")
    result = subprocess.run([sys.executable, "inference.py"], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        _fail(f"inference.py failed in mock mode:\n{result.stdout}\n{result.stderr}")
    if "[START]" not in result.stdout or "[STEP]" not in result.stdout or "[END]" not in result.stdout:
        _fail("inference.py must emit [START], [STEP], [END] structured logs")

    artifact = Path("baseline_scores.json")
    if not artifact.exists():
        _fail("baseline_scores.json was not generated")
    json.loads(artifact.read_text(encoding="utf-8"))
    _ok("inference.py reproduces baseline and writes baseline_scores.json")


def check_docker() -> None:
    if shutil.which("docker") is None:
        print("[SKIP] Docker CLI not found locally. Remote validation will still run Docker build.")
        return
    cmd = ["docker", "build", "-t", "support-ticket-env-local-check", "."]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        _fail(f"Docker build failed:\n{result.stdout}\n{result.stderr}")
    _ok("Dockerfile builds locally")


def main() -> None:
    check_files()
    check_openenv_spec()
    check_api_endpoints()
    check_tasks_and_graders()
    check_inference_mock()
    check_docker()
    print("[PASS] Pre-submission checks completed")


if __name__ == "__main__":
    main()