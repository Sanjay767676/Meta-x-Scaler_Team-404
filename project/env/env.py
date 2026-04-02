"""
SupportEnv — OpenEnv-style environment for AI support ticket resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .dataset import TICKETS
from .models import Action, Observation, Reward


# ---------------------------------------------------------------------------
# Internal ticket schema — built from dataset.py
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
        ticket_id=t["id"],
        user_query=t["query"],
        expected_category=t["category"],
        expected_priority=t["priority"],
        expected_action=t["action"],
    )
    for t in TICKETS
]

MAX_STEPS: int = 5

# ---------------------------------------------------------------------------
# Reward weights
# ---------------------------------------------------------------------------

_W_CATEGORY = 0.3   # correct category
_W_PRIORITY  = 0.2   # correct priority
_W_ACTION    = 0.3   # correct action type
_W_KEYWORDS  = 0.2   # response contains useful keywords

_PENALTY_ALL_WRONG = 0.2  # deducted when category, priority, AND action are all wrong

# Keywords that signal a useful response for each action type.
# Scoring: at least 1 keyword present → full keyword credit.
_ACTION_KEYWORDS: dict[str, list[str]] = {
    "refund": [
        "refund", "reimburs", "charg", "payment", "credit", "return",
        "amount", "transaction",
    ],
    "escalate": [
        "escalat", "team", "specialist", "engineer", "investigat",
        "urgent", "priorit", "senior", "handl",
    ],
    "guide": [
        "step", "follow", "guid", "instruction", "how", "navig",
        "click", "setting", "menu", "select",
    ],
}


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
        Deterministic partial scoring.

        Breakdown
        ---------
        +0.3  category correct
        +0.2  priority correct
        +0.3  action type correct
        +0.2  response contains at least one useful keyword
        -0.2  penalty if ALL THREE of category, priority, and action are wrong

        Final score is clamped to [0.0, 1.0].
        """
        assert self._ticket is not None
        t = self._ticket

        score = 0.0
        reasons: list[str] = []

        # --- Category (+0.3) ---
        category_correct = action.category.lower() == t.expected_category
        if category_correct:
            score += _W_CATEGORY
            reasons.append(f"category correct (+{_W_CATEGORY})")
        else:
            reasons.append(
                f"category wrong: got '{action.category}', "
                f"expected '{t.expected_category}' (+0.0)"
            )

        # --- Priority (+0.2) ---
        priority_correct = action.priority.lower() == t.expected_priority
        if priority_correct:
            score += _W_PRIORITY
            reasons.append(f"priority correct (+{_W_PRIORITY})")
        else:
            reasons.append(
                f"priority wrong: got '{action.priority}', "
                f"expected '{t.expected_priority}' (+0.0)"
            )

        # --- Action type (+0.3) ---
        action_correct = action.action.lower() == t.expected_action
        if action_correct:
            score += _W_ACTION
            reasons.append(f"action correct: '{action.action}' (+{_W_ACTION})")
        else:
            reasons.append(
                f"action wrong: got '{action.action}', "
                f"expected '{t.expected_action}' (+0.0)"
            )

        # --- Keyword check (+0.2) ---
        # Use the expected action's keyword list so scoring is deterministic
        # regardless of what action the agent chose.
        keywords = _ACTION_KEYWORDS.get(t.expected_action, [])
        response_lower = action.response.lower()
        matched = [kw for kw in keywords if kw in response_lower]
        if matched:
            score += _W_KEYWORDS
            reasons.append(
                f"response keywords matched {matched} (+{_W_KEYWORDS})"
            )
        else:
            reasons.append(f"no useful keywords found in response (+0.0)")

        # --- Penalty: all three main dimensions wrong (-0.2) ---
        if not category_correct and not priority_correct and not action_correct:
            score -= _PENALTY_ALL_WRONG
            reasons.append(f"completely wrong: penalty (-{_PENALTY_ALL_WRONG})")

        # Clamp to [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        return Reward(score=round(score, 4), reason="; ".join(reasons))
