"""
SupportEnv — OpenEnv-style environment for AI support ticket resolution.
"""

from __future__ import annotations

from typing import Optional

from .dataset import TICKETS
from .graders import ACTION_KEYWORDS, grade
from .models import Action, Observation, Reward
from .tasks import TASKS


MAX_STEPS: int = 5

# ---------------------------------------------------------------------------
# Reward weights
# ---------------------------------------------------------------------------

_W_CATEGORY = 0.3   # correct category
_W_PRIORITY  = 0.2   # correct priority
_W_ACTION    = 0.3   # correct action type
_W_KEYWORDS  = 0.2   # response contains useful keywords

_PENALTY_ALL_WRONG = 0.2  # deducted when category, priority, AND action are all wrong
_PENALTY_PREMATURE_RESOLVE = 0.25

# Imported from graders.py — single source of truth for keyword scoring.
_ACTION_KEYWORDS = ACTION_KEYWORDS


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
        self._ticket: Optional[dict] = None
        self._step_count: int = 0
        self._conversation_history: list[str] = []
        self._done: bool = False
        self._ticket_index: int = 0
        self._task_id: str = "hard"
        self._hard_phase: str = "diagnose"

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self, ticket_index: int = 0, task_id: Optional[str] = None) -> Observation:
        """
        Load a ticket from the hardcoded dataset and reset internal state.

        Parameters
        ----------
        ticket_index : int
            Index into the dataset (0-based). Wraps around if out of range.
        task_id : Optional[str]
            Optional task difficulty selector: "easy", "medium", or "hard".
            If provided, task metadata chooses the ticket.

        Returns
        -------
        Observation
            Initial observation for the loaded ticket.
        """
        if task_id is not None:
            if task_id not in TASKS:
                raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS)}")
            self._task_id = task_id
            self._ticket_index = TASKS[task_id].ticket_index % len(TICKETS)
        else:
            self._ticket_index = ticket_index % len(TICKETS)

        self._ticket = TICKETS[self._ticket_index]
        self._step_count = 0
        self._conversation_history = []
        self._done = False
        self._hard_phase = "diagnose"
        return self._build_observation()

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
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
        info : dict
            Auxiliary diagnostic data (step count, ticket id, reason).
        """
        if self._ticket is None:
            raise RuntimeError("Environment not initialised. Call reset() before step().")
        if self._done:
            raise RuntimeError("Episode is already done. Call reset() to start a new one.")

        self._step_count += 1

        # Record this turn in the conversation history
        self._conversation_history.append(f"agent: {action.response}")

        reward = self._score_action(action)

        # Hard mode requires at least one diagnosis turn before final resolution.
        if self._task_id == "hard":
            was_diagnose = self._hard_phase == "diagnose"
            triage_ok = (
                action.category.lower() == self._ticket["category"]
                and action.priority.lower() == self._ticket["priority"]
            )
            if was_diagnose and triage_ok:
                self._hard_phase = "resolve"

            if action.resolve and was_diagnose:
                adjusted = max(0.0, reward.score - _PENALTY_PREMATURE_RESOLVE)
                reason = (reward.reason or "") + f"; premature resolve in hard mode (-{_PENALTY_PREMATURE_RESOLVE})"
                reward = Reward(score=round(adjusted, 4), reason=reason.strip("; "))

            if self._hard_phase == "resolve" and action.resolve and not was_diagnose:
                self._done = True
        else:
            if action.resolve:
                self._done = True

        if self._step_count >= MAX_STEPS:
            self._done = True

        observation = self._build_observation()

        info: dict = {
            "step": self._step_count,
            "max_steps": MAX_STEPS,
            "ticket_id": self._ticket["id"],
            "task_id": self._task_id,
            "reward_reason": reward.reason,
        }

        return observation, reward, self._done, info

    def state(self) -> dict:
        """
        Return a plain-dict snapshot of the current environment state.
        """
        if self._ticket is None:
            return {"status": "not_started"}
        return {
            "ticket_id": self._ticket["id"],
            "step": self._step_count,
            "max_steps": MAX_STEPS,
            "done": self._done,
            "task_id": self._task_id,
            "hard_phase": self._hard_phase,
            "conversation_history": list(self._conversation_history),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_observation(self) -> Observation:
        if self._ticket is None:
            raise RuntimeError("No active ticket. Call reset() first.")
        return Observation(
            ticket_id=self._ticket["id"],
            user_query=self._ticket["query"],
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
        if self._ticket is None:
            raise RuntimeError("No active ticket. Call reset() first.")
        t = self._ticket
        score = grade(self._task_id, action, t)

        reasons: list[str] = []
        category_correct = action.category.lower() == t["category"]
        priority_correct = action.priority.lower() == t["priority"]
        action_correct = action.action.lower() == t["action"]

        if category_correct:
            reasons.append(f"category correct (+{_W_CATEGORY})")
        else:
            reasons.append(f"category wrong: got '{action.category}', expected '{t['category']}'")

        if self._task_id in ("medium", "hard"):
            if priority_correct:
                reasons.append(f"priority correct (+{_W_PRIORITY})")
            else:
                reasons.append(f"priority wrong: got '{action.priority}', expected '{t['priority']}'")

        if self._task_id == "hard":
            if action_correct:
                reasons.append(f"action correct: '{action.action}' (+{_W_ACTION})")
            else:
                reasons.append(f"action wrong: got '{action.action}', expected '{t['action']}'")

        keywords = _ACTION_KEYWORDS.get(t["action"], [])
        response_lower = action.response.lower()
        matched = [kw for kw in keywords if kw in response_lower]
        if self._task_id == "hard":
            if matched:
                reasons.append(f"response keywords matched {matched} (+{_W_KEYWORDS})")
            else:
                reasons.append("no useful keywords found in response")

            if not category_correct and not priority_correct and not action_correct:
                reasons.append(f"completely wrong: penalty (-{_PENALTY_ALL_WRONG})")

        # Penalize repeated identical responses to discourage looping behavior.
        if len(self._conversation_history) >= 2:
            if self._conversation_history[-1] == self._conversation_history[-2]:
                score = max(0.0, score - 0.1)
                reasons.append("looping response pattern: penalty (-0.1)")

        return Reward(score=round(score, 4), reason="; ".join(reasons))
