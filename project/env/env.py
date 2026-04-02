"""
Support Ticket Environment — OpenEnv-compatible environment definition.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    Action,
    Message,
    Observation,
    StepResult,
    Ticket,
    TicketStatus,
)


class SupportTicketEnv:
    """
    OpenEnv-compatible environment for support ticket resolution tasks.

    An agent interacts with a support ticket by reading ticket details,
    sending messages, and taking resolution actions. The episode ends when
    the ticket is closed or the step limit is reached.
    """

    def __init__(self, max_steps: int = 20) -> None:
        self.max_steps = max_steps
        self._current_step: int = 0
        self._ticket: Optional[Ticket] = None
        self._conversation: list[Message] = []

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self, ticket: Ticket) -> Observation:
        """Reset the environment with a new ticket and return the initial observation."""
        self._ticket = ticket
        self._conversation = []
        self._current_step = 0
        return self._build_observation()

    def step(self, action: Action) -> StepResult:
        """Apply an action and return the next observation, reward, done flag, and info."""
        if self._ticket is None:
            raise RuntimeError("Environment not reset. Call reset() before step().")

        self._current_step += 1
        # TODO: implement action dispatch
        observation = self._build_observation()
        reward = 0.0
        done = self._is_done()
        return StepResult(observation=observation, reward=reward, done=done)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_observation(self) -> Observation:
        return Observation(
            ticket=self._ticket,
            conversation=list(self._conversation),
            metadata={"step": self._current_step},
        )

    def _is_done(self) -> bool:
        if self._ticket is None:
            return False
        terminal_statuses = {TicketStatus.resolved, TicketStatus.closed}
        return (
            self._ticket.status in terminal_statuses
            or self._current_step >= self.max_steps
        )
