"""
inference.py — Example script for running an agent against SupportEnv.

Usage:
    python inference.py
"""

from __future__ import annotations

from env import SupportEnv, Action


def run_episode(ticket_index: int = 0) -> None:
    env = SupportEnv()
    obs = env.reset(ticket_index=ticket_index)

    print(f"[Episode start]")
    print(f"  Ticket ID : {obs.ticket_id}")
    print(f"  Query     : {obs.user_query}")
    print()

    done = False
    total_reward = 0.0

    while not done:
        # TODO: replace with a real agent policy
        action = Action(
            category="billing",
            priority="high",
            action="refund",
            response="We have identified the duplicate charge and will process a refund within 3-5 business days.",
            resolve=True,
        )

        obs, reward, done = env.step(action)
        total_reward += reward.score

        state = env.state()
        print(
            f"  Step {state['step']:>2} | "
            f"score={reward.score:.4f} | "
            f"done={done}"
        )
        print(f"    {reward.reason}")

    print()
    print(f"[Episode end] Total reward: {total_reward:.4f}")


if __name__ == "__main__":
    run_episode(ticket_index=0)
