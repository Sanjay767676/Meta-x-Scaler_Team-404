"""
Grading functions for the Support Ticket Environment.

Each grader takes a predicted Action and an expected dict (one row from
TICKETS) and returns a float score in (0.0, 1.0).

Difficulty    Scored fields                        Weights
-----------   -----------------------------------  ---------------------------
easy          category                             1.0
medium        category, priority                   0.6 + 0.4
hard          category, priority, action, response 0.3 + 0.2 + 0.3 + 0.2
              penalty if all three main fields wrong: -0.2, clamped then mapped to (0, 1)
"""

from __future__ import annotations

from .models import Action


MIN_STRICT_SCORE = 0.01
MAX_STRICT_SCORE = 0.99


# ---------------------------------------------------------------------------
# Shared constants — imported by env.py to keep scoring in sync
# ---------------------------------------------------------------------------

ACTION_KEYWORDS: dict[str, list[str]] = {
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
# Internal helpers
# ---------------------------------------------------------------------------

def _keyword_hit(response: str, expected_action: str) -> bool:
    """Return True if the response contains at least one keyword for the action."""
    keywords = ACTION_KEYWORDS.get(expected_action, [])
    lower = response.lower()
    return any(kw in lower for kw in keywords)


def _to_open_interval(score: float) -> float:
    """Clamp any raw score to a strict open interval (0, 1)."""
    clamped = max(0.0, min(1.0, float(score)))
    if clamped <= 0.0:
        return MIN_STRICT_SCORE
    if clamped >= 1.0:
        return MAX_STRICT_SCORE
    return round(clamped, 4)


# ---------------------------------------------------------------------------
# Graders
# ---------------------------------------------------------------------------

def grade_easy(action: Action, expected: dict) -> float:
    """
    Easy task — classify category only.

    Scoring
    -------
    +0.99 category correct
    +0.01 category wrong

    Returns a score in {0.01, 0.99}.
    """
    return MAX_STRICT_SCORE if action.category.lower() == expected["category"] else MIN_STRICT_SCORE


def grade_medium(action: Action, expected: dict) -> float:
    """
    Medium task — classify category and assign priority.

    Scoring
    -------
    +0.6  category correct
    +0.4  priority correct

    Returns a score in (0.0, 1.0).
    """
    score = 0.0

    if action.category.lower() == expected["category"]:
        score += 0.6

    if action.priority.lower() == expected["priority"]:
        score += 0.4

    return _to_open_interval(score)


def grade_hard(action: Action, expected: dict) -> float:
    """
    Hard task — full resolution (category, priority, action, response).

    Scoring
    -------
    +0.3  category correct
    +0.2  priority correct
    +0.3  action correct
    +0.2  response contains at least one keyword for the expected action
    -0.2  penalty if category, priority, AND action are all wrong

    Final score is clamped then mapped to (0.0, 1.0).
    """
    category_correct = action.category.lower() == expected["category"]
    priority_correct = action.priority.lower() == expected["priority"]
    action_correct   = action.action.lower()   == expected["action"]
    keywords_hit     = _keyword_hit(action.response, expected["action"])

    score = 0.0

    if category_correct:
        score += 0.3
    if priority_correct:
        score += 0.2
    if action_correct:
        score += 0.3
    if keywords_hit:
        score += 0.2

    # Penalty when all three primary fields are wrong
    if not category_correct and not priority_correct and not action_correct:
        score -= 0.2

    return _to_open_interval(score)


# ---------------------------------------------------------------------------
# Dispatch helper
# ---------------------------------------------------------------------------

def grade(difficulty: str, action: Action, expected: dict) -> float:
    """
    Route to the correct grader by difficulty string.

    Parameters
    ----------
    difficulty : str
        One of "easy", "medium", "hard".
    action : Action
        The agent's predicted action.
    expected : dict
        One row from TICKETS with keys: id, query, category, priority, action.

    Returns
    -------
    float
        Score in (0.0, 1.0).
    """
    graders = {
        "easy":   grade_easy,
        "medium": grade_medium,
        "hard":   grade_hard,
    }
    if difficulty not in graders:
        raise ValueError(
            f"Unknown difficulty '{difficulty}'. Choose from: {list(graders)}"
        )
    return graders[difficulty](action, expected)
