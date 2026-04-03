"""
Task definitions for the Support Ticket Environment.

Three difficulty levels are provided. Each task narrows or broadens
what the agent is expected to produce and which fields are scored.

Difficulty    Scored fields
-----------   ---------------------------------------------------
easy          category only
medium        category + priority
hard          category + priority + action + response (keywords)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------------

class Task(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    difficulty: Literal["easy", "medium", "hard"]
    objective: str = Field(..., description="One-line goal the agent must achieve")
    description: str = Field(..., description="Full instructions shown to the agent")
    scored_fields: list[str] = Field(
        ...,
        description="Action fields that count toward the reward for this task",
    )
    ticket_index: int = Field(
        default=0,
        description="Index into the dataset to use for this task (0-based)",
    )


# ---------------------------------------------------------------------------
# Task catalogue
# ---------------------------------------------------------------------------

TASKS: dict[str, Task] = {
    "easy": Task(
        task_id="easy",
        difficulty="easy",
        objective="Classify the support ticket into the correct category.",
        description=(
            "You will be shown a customer support ticket. "
            "Your only goal is to identify which category the ticket belongs to.\n\n"
            "Valid categories: billing, account, technical\n\n"
            "You will be scored solely on whether your 'category' field is correct. "
            "Fill in the remaining Action fields with any placeholder values — "
            "they will not affect your score."
        ),
        scored_fields=["category"],
        ticket_index=2,
    ),

    "medium": Task(
        task_id="medium",
        difficulty="medium",
        objective="Classify the ticket's category and assign the correct priority.",
        description=(
            "You will be shown a customer support ticket. "
            "Your goal is to correctly identify both the category and the priority.\n\n"
            "Valid categories: billing, account, technical\n"
            "Valid priorities: low, medium, high\n\n"
            "Scoring:\n"
            "  +0.3  category correct\n"
            "  +0.2  priority correct\n\n"
            "Fill in the remaining Action fields with any placeholder values — "
            "they will not affect your score."
        ),
        scored_fields=["category", "priority"],
        ticket_index=1,
    ),

    "hard": Task(
        task_id="hard",
        difficulty="hard",
        objective=(
            "Fully resolve the ticket: correct category, priority, action, "
            "and a helpful response."
        ),
        description=(
            "You will be shown a customer support ticket. "
            "Your goal is to produce a complete, multi-step resolution.\n\n"
            "Valid categories: billing, account, technical\n"
            "Valid priorities: low, medium, high\n"
            "Valid actions: refund, escalate, guide\n\n"
            "Hard-mode flow:\n"
            "  Step 1: diagnosis and triage (resolve should be false)\n"
            "  Step 2+: final resolution after a solid diagnosis\n\n"
            "Scoring:\n"
            "  +0.3  category correct\n"
            "  +0.2  priority correct\n"
            "  +0.3  action correct\n"
            "  +0.2  response contains useful keywords for the action\n"
            "  -0.25 penalty for resolving too early in hard mode\n"
            "  -0.2  penalty if category, priority, AND action are all wrong\n\n"
            "Set 'resolve' to True only when you are confident the issue is addressed. "
            "Write a clear, empathetic response that uses language appropriate to the "
            "chosen action (e.g. mention refund steps, escalation process, or how-to "
            "guidance)."
        ),
        scored_fields=["category", "priority", "action", "response"],
        ticket_index=12,
    ),
}
