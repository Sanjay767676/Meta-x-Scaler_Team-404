"""
SupportEnv — OpenEnv-style environment for AI support ticket resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import Action, Observation, Reward


# ---------------------------------------------------------------------------
# Internal ticket schema (hardcoded dataset)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Ticket:
    ticket_id: str
    user_query: str
    expected_category: str
    expected_priority: str
    expected_action: str   # "refund" | "escalate" | "guide"


_DATASET: list[_Ticket] = [
    _Ticket(
        ticket_id="T001",
        user_query="I was charged twice for my subscription last month. Please fix this.",
        expected_category="billing",
        expected_priority="high",
        expected_action="refund",
    ),
    _Ticket(
        ticket_id="T002",
        user_query="My account has been locked and I cannot reset my password.",
        expected_category="account",
        expected_priority="high",
        expected_action="escalate",
    ),
    _Ticket(
        ticket_id="T003",
        user_query="How do I export my data to a CSV file?",
        expected_category="technical",
        expected_priority="low",
        expected_action="guide",
    ),
    _Ticket(
        ticket_id="T004",
        user_query="I want to cancel my plan and get a prorated refund.",
        expected_category="billing",
        expected_priority="medium",
        expected_action="refund",
    ),
    _Ticket(
        ticket_id="T005",
        user_query="The API is returning 500 errors in production for all our requests.",
        expected_category="technical",
        expected_priority="high",
        expected_action="escalate",
    ),
]

MAX_STEPS: int = 5

# ---------------------------------------------------------------------------
# Reward weights (must sum to 1.0)
# ---------------------------------------------------------------------------

_W_CATEGORY = 0.25
_W_PRIORITY  = 0.25
_W_ACTION    = 0.35
_W_RESOLVE   = 0.15


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class SupportEnv:
    """
    OpenEnv-style environment for support ticket resolution.

    Episode flow
    ------------
    1. Call reset() to load a ticket and get the initial Observation.
    2. Call step(action) each turn; receive (Observation, Reward, done).
    3. The episode ends when action.resolve is True or MAX_STEPS is reached.
    """

    def __init__(self) -> None:
        self._ticket: Optional[_Ticket] = None
        self._step_count: int = 0
        self._conversation_history: list[str] = []
        self._done: bool = False
        self._ticket_index: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self, ticket_index: int = 0) -> Observation:
        """
        Load a ticket from the hardcoded dataset and reset internal state.

        Parameters
        ----------
        ticket_index : int
            Index into the dataset (0-based). Wraps around if out of range.

        Returns
        -------
        Observation
            Initial observation for the loaded ticket.
        """
        self._ticket_index = ticket_index % len(_DATASET)
        self._ticket = _DATASET[self._ticket_index]
        self._step_count = 0
        self._conversation_history = []
        self._done = False
        return self._build_observation()

    def step(self, action: Action) -> tuple[Observation, Reward, bool]:
        """
        Apply an action and advance the environment by one step.

        Parameters
        ----------
        action : Action
            The agent's response and decisions for this turn.

        Returns
        -------
        observation : Observation
            Updated environment state visible to the agent.
        reward : Reward
            Partial score in [0, 1] with an explanation.
        done : bool
            True when the episode is finished.
        """
        if self._ticket is None or self._done:
            raise RuntimeError("Call reset() before step(), or episode is already done.")

        self._step_count += 1

        # Record this turn in the conversation history
        self._conversation_history.append(f"agent: {action.response}")

        reward = self._score_action(action)

        # Episode ends if agent resolves the ticket or the step limit is hit
        if action.resolve or self._step_count >= MAX_STEPS:
            self._done = True

        observation = self._build_observation()
        return observation, reward, self._done

    def state(self) -> dict:
        """
        Return a plain-dict snapshot of the current environment state.
        """
        if self._ticket is None:
            return {"status": "not_started"}
        return {
            "ticket_id": self._ticket.ticket_id,
            "step": self._step_count,
            "max_steps": MAX_STEPS,
            "done": self._done,
            "conversation_history": list(self._conversation_history),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_observation(self) -> Observation:
        assert self._ticket is not None
        return Observation(
            ticket_id=self._ticket.ticket_id,
            user_query=self._ticket.user_query,
            category=None,          # agent must infer category
            priority=None,          # agent must infer priority
            conversation_history=list(self._conversation_history),
        )

    def _score_action(self, action: Action) -> Reward:
        """
        Deterministic partial scoring. Each dimension is worth a fixed weight.

        Scoring breakdown
        -----------------
        category correct  →  0.25
        priority correct  →  0.25
        action correct    →  0.35
        resolve correct   →  0.15  (should_resolve == action.resolve)

        Total max = 1.0
        """
        assert self._ticket is not None
        t = self._ticket

        # Determine whether resolving right now is the ideal move:
        # ideal to resolve only when the action itself is correct AND
        # this is either the final step or the action is genuinely sufficient.
        correct_action = action.action.lower() == t.expected_action
        should_resolve = correct_action and (
            self._step_count >= MAX_STEPS or action.resolve
        )

        score = 0.0
        reasons: list[str] = []

        # Category
        if action.category.lower() == t.expected_category:
            score += _W_CATEGORY
            reasons.append("category correct (+0.25)")
        else:
            reasons.append(
                f"category wrong: got '{action.category}', "
                f"expected '{t.expected_category}' (+0.00)"
            )

        # Priority
        if action.priority.lower() == t.expected_priority:
            score += _W_PRIORITY
            reasons.append("priority correct (+0.25)")
        else:
            reasons.append(
                f"priority wrong: got '{action.priority}', "
                f"expected '{t.expected_priority}' (+0.00)"
            )

        # Action type
        if correct_action:
            score += _W_ACTION
            reasons.append(f"action correct: '{action.action}' (+0.35)")
        else:
            reasons.append(
                f"action wrong: got '{action.action}', "
                f"expected '{t.expected_action}' (+0.00)"
            )

        # Resolve flag
        if action.resolve == should_resolve:
            score += _W_RESOLVE
            reasons.append("resolve flag correct (+0.15)")
        else:
            reasons.append("resolve flag incorrect (+0.00)")

        return Reward(score=round(score, 4), reason="; ".join(reasons))
