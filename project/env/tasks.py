"""
Task definitions for the Support Ticket Environment.

A task bundles a ticket scenario with any context the agent needs.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .models import Ticket, TicketPriority, TicketStatus


class Task(BaseModel):
    task_id: str = Field(..., description="Unique identifier for this task")
    description: str = Field(..., description="Human-readable task description")
    ticket: Ticket = Field(..., description="The support ticket to resolve")
    context: dict = Field(default_factory=dict, description="Extra context for the task")
    max_steps: int = Field(default=20, description="Step limit for the episode")


def make_task(
    task_id: str,
    title: str,
    description: str,
    priority: TicketPriority = TicketPriority.medium,
    context: Optional[dict] = None,
    max_steps: int = 20,
) -> Task:
    """Convenience factory for creating a Task with a new Ticket."""
    import uuid

    ticket = Ticket(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        priority=priority,
        status=TicketStatus.open,
    )
    return Task(
        task_id=task_id,
        description=f"Resolve ticket: {title}",
        ticket=ticket,
        context=context or {},
        max_steps=max_steps,
    )


# ---------------------------------------------------------------------------
# Sample task catalogue — replace / extend as needed
# ---------------------------------------------------------------------------

SAMPLE_TASKS: list[Task] = [
    make_task(
        task_id="task-001",
        title="Cannot log in to account",
        description=(
            "The customer reports that they are unable to log into their account "
            "after resetting their password. They receive an 'invalid credentials' "
            "error on every attempt."
        ),
        priority=TicketPriority.high,
    ),
    make_task(
        task_id="task-002",
        title="Billing charge discrepancy",
        description=(
            "Customer was charged twice for a single subscription renewal on 2024-03-01. "
            "They are requesting a refund for the duplicate charge."
        ),
        priority=TicketPriority.critical,
    ),
    make_task(
        task_id="task-003",
        title="Feature request: dark mode",
        description=(
            "The customer would like a dark mode option added to the dashboard. "
            "They find the current light theme strains their eyes during long sessions."
        ),
        priority=TicketPriority.low,
    ),
]
