"""
Pydantic models for the AI Support Ticket Environment.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    ticket_id: str = Field(..., description="Unique identifier for the support ticket")
    user_query: str = Field(..., description="The user's message or question")
    category: Optional[str] = Field(default=None, description="Ticket category (e.g. billing, technical)")
    priority: Optional[str] = Field(default=None, description="Ticket priority (e.g. low, medium, high)")
    conversation_history: list[str] = Field(
        default_factory=list,
        description="Ordered list of previous messages in the conversation",
    )


class Action(BaseModel):
    category: str = Field(..., description="Category assigned to the ticket")
    priority: str = Field(..., description="Priority assigned to the ticket")
    action: str = Field(..., description="Action to take: 'refund', 'escalate', or 'guide'")
    response: str = Field(..., description="The agent's response to the user")
    resolve: bool = Field(..., description="Whether this action resolves the ticket")


class Reward(BaseModel):
    score: float = Field(..., description="Numeric reward signal for the agent's action")
    reason: Optional[str] = Field(default=None, description="Human-readable explanation of the reward")
