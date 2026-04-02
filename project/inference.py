"""
inference.py — Run an agent episode against SupportEnv.

Usage:
    python inference.py
"""

from __future__ import annotations

from env import SupportEnv, Action


# ---------------------------------------------------------------------------
# Model output parser
# ---------------------------------------------------------------------------

def parse_model_output(raw: str) -> Action:
    """
    Convert a model's raw string output into a typed Action object.

    Expected format (one key: value pair per line):
        category: billing
        priority: high
        action: refund
        response: We will process a full refund within 3-5 business days.
        resolve: true

    Lines that cannot be parsed are silently skipped.
    Missing required fields fall back to safe defaults.
    """
    fields: dict[str, str] = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()

    return Action(
        category=fields.get("category", "unknown"),
        priority=fields.get("priority", "medium"),
        action=fields.get("action", "guide"),
        response=fields.get("response", ""),
        resolve=fields.get("resolve", "false").lower() == "true",
    )


# ---------------------------------------------------------------------------
# Placeholder model — replace with a real LLM call
# ---------------------------------------------------------------------------

def call_model(obs_text: str) -> str:
    """
    Simulate a model call. Returns a raw string in the expected key: value format.
    Replace this function body with a real LLM API call.
    """
    return (
        "category: billing\n"
        "priority: high\n"
        "action: refund\n"
        "response: We have identified the duplicate charge and will process "
        "a full refund to your original payment method within 3-5 business days.\n"
        "resolve: true"
    )


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------

def run_episode(ticket_index: int = 0) -> float:
    env = SupportEnv()
    obs = env.reset(ticket_index=ticket_index)

    print(f"[START] ticket_id={obs.ticket_id} | query=\"{obs.user_query}\"")

    total_reward = 0.0
    done = False

    while not done:
        # Build a text prompt from the current observation
        obs_text = (
            f"ticket_id: {obs.ticket_id}\n"
            f"query: {obs.user_query}\n"
            f"history: {obs.conversation_history}"
        )

        # Get raw model output and parse it into an Action
        raw_output = call_model(obs_text)
        action = parse_model_output(raw_output)

        obs, reward, done, info = env.step(action)
        total_reward += reward.score

        print(
            f"[STEP {info['step']}] "
            f"category={action.category} | "
            f"priority={action.priority} | "
            f"action={action.action} | "
            f"resolve={action.resolve} | "
            f"score={reward.score:.4f}"
        )
        print(f"         reason: {reward.reason}")

    print(f"[END] total_reward={total_reward:.4f} | steps={info['step']}")
    return total_reward


if __name__ == "__main__":
    run_episode(ticket_index=0)
