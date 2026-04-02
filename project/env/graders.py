"""
Graders for evaluating agent performance on support ticket tasks.

Each grader takes a completed episode and returns a score between 0 and 1.
"""

from __future__ import annotations

from typing import Callable

from .models import Observation, StepResult, TicketStatus


GraderFn = Callable[[list[StepResult]], float]


# ---------------------------------------------------------------------------
# Individual grader functions
# ---------------------------------------------------------------------------

def resolution_grader(results: list[StepResult]) -> float:
    """
    Returns 1.0 if the ticket was resolved/closed by end of episode, else 0.0.
    """
    if not results:
        return 0.0
    final = results[-1]
    terminal = {TicketStatus.resolved, TicketStatus.closed}
    return 1.0 if final.observation.ticket.status in terminal else 0.0


def efficiency_grader(results: list[StepResult], max_steps: int = 20) -> float:
    """
    Returns a score based on how quickly the ticket was resolved.
    Fewer steps → higher score. Returns 0 if not resolved.
    """
    if not results:
        return 0.0
    if resolution_grader(results) == 0.0:
        return 0.0
    steps_taken = len(results)
    return max(0.0, 1.0 - (steps_taken - 1) / max(max_steps - 1, 1))


def customer_satisfaction_grader(results: list[StepResult]) -> float:
    """
    Placeholder: evaluate whether the agent's messages were polite and helpful.
    Returns a score in [0, 1]. Override with a model-based grader as needed.
    """
    # TODO: implement grading logic (e.g. via an LLM judge or rule-based check)
    return 0.0


# ---------------------------------------------------------------------------
# Composite grader
# ---------------------------------------------------------------------------

def composite_grader(
    results: list[StepResult],
    max_steps: int = 20,
    weights: dict[str, float] | None = None,
) -> float:
    """
    Weighted combination of individual graders.

    Default weights:
        resolution: 0.5
        efficiency: 0.3
        customer_satisfaction: 0.2
    """
    default_weights: dict[str, float] = {
        "resolution": 0.5,
        "efficiency": 0.3,
        "customer_satisfaction": 0.2,
    }
    w = {**default_weights, **(weights or {})}

    scores = {
        "resolution": resolution_grader(results),
        "efficiency": efficiency_grader(results, max_steps=max_steps),
        "customer_satisfaction": customer_satisfaction_grader(results),
    }

    total_weight = sum(w[k] for k in scores)
    return sum(w[k] * v for k, v in scores.items()) / total_weight if total_weight else 0.0
