"""
Pydantic models for the Support Ticket Environment.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Ticket(BaseModel):
    id: str = Field(..., description="Unique ticket identifier")
    title: str = Field(..., description="Short summary of the issue")
    description: str = Field(..., description="Full description of the issue")
    priority: TicketPriority = Field(default=TicketPriority.medium)
    status: TicketStatus = Field(default=TicketStatus.open)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class Message(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Observation(BaseModel):
    ticket: Ticket
    conversation: list[Message] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class Action(BaseModel):
    action_type: str = Field(..., description="Type of action to take")
    parameters: dict = Field(default_factory=dict, description="Action parameters")


class StepResult(BaseModel):
    observation: Observation
    reward: float = Field(default=0.0)
    done: bool = Field(default=False)
    info: dict = Field(default_factory=dict)
