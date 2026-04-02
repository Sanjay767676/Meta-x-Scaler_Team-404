"""
inference.py — Example script for running an agent against the Support Ticket Environment.

Usage:
    python inference.py
"""

from __future__ import annotations

from env import SupportTicketEnv, Action, SAMPLE_TASKS
from env.graders import composite_grader


def run_episode(task_index: int = 0) -> None:
    task = SAMPLE_TASKS[task_index]
    env = SupportTicketEnv(max_steps=task.max_steps)

    observation = env.reset(ticket=task.ticket)
    print(f"[Episode start] Ticket: {observation.ticket.title}")
    print(f"  Priority : {observation.ticket.priority}")
    print(f"  Status   : {observation.ticket.status}")
    print()

    results = []
    done = False

    while not done:
        # TODO: replace with a real agent policy
        action = Action(action_type="no_op")

        result = env.step(action)
        results.append(result)
        done = result.done

        print(
            f"  Step {result.observation.metadata['step']:>3} | "
            f"status={result.observation.ticket.status} | "
            f"reward={result.reward:.3f} | done={result.done}"
        )

    score = composite_grader(results, max_steps=task.max_steps)
    print()
    print(f"[Episode end] Composite score: {score:.4f}")


if __name__ == "__main__":
    run_episode(task_index=0)
