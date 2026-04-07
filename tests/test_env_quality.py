"""Quality and reproducibility tests for support-ticket OpenEnv environment."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import Action, SupportEnv, TASKS, TICKETS, grade


def test_graders_are_deterministic_for_same_input() -> None:
    expected = TICKETS[TASKS["hard"].ticket_index]
    action = Action(
        category=expected["category"],
        priority=expected["priority"],
        action=expected["action"],
        response="We escalated this issue and will share updates.",
        resolve=False,
    )

    scores = [grade("hard", action, expected) for _ in range(10)]
    assert len(set(scores)) == 1, f"Expected deterministic scores, got {scores}"


def test_hard_mode_penalizes_premature_resolution() -> None:
    env = SupportEnv()
    env.reset(task_id="hard")

    premature = Action(
        category="technical",
        priority="high",
        action="escalate",
        response="We escalated this issue to specialists.",
        resolve=True,
    )
    _, reward, done, _ = env.step(premature)

    assert done is False, "Hard mode should not finish on first premature resolve"
    assert "premature resolve" in (reward.reason or "").lower()


def test_reward_signal_varies_across_trajectory() -> None:
    env = SupportEnv()
    env.reset(task_id="hard")

    action = Action(
        category="technical",
        priority="high",
        action="escalate",
        response="We escalated this issue to specialists.",
        resolve=False,
    )

    _, reward_1, _, _ = env.step(action)
    _, reward_2, _, _ = env.step(action)

    assert reward_1.score != reward_2.score, "Expected trajectory shaping to vary reward across steps"


def test_compound_ticket_under_triage_penalty_triggers() -> None:
    env = SupportEnv()
    env.reset(task_id="hard")

    # Ticket 13 is compound and should prefer escalate in hard mode.
    wrong_action = Action(
        category="technical",
        priority="high",
        action="guide",
        response="Please follow these steps in settings.",
        resolve=False,
    )

    _, reward, _, _ = env.step(wrong_action)
    assert "compound ticket under-triaged" in (reward.reason or "")
