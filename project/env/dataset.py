"""
Hardcoded support ticket dataset.

Each ticket contains:
- id       : unique ticket identifier
- query    : the user's message
- category : correct category  ("billing" | "account" | "technical")
- priority : correct priority  ("low" | "medium" | "high")
- action   : correct action    ("refund" | "escalate" | "guide")
"""

from __future__ import annotations

TICKETS: list[dict] = [
    {
        "id": "1",
        "query": "Payment failed but money deducted",
        "category": "billing",
        "priority": "high",
        "action": "refund",
    },
    {
        "id": "2",
        "query": "My account is locked and I cannot reset my password",
        "category": "account",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "3",
        "query": "How do I export my data to a CSV file?",
        "category": "technical",
        "priority": "low",
        "action": "guide",
    },
    {
        "id": "4",
        "query": "I want to cancel my subscription and get a prorated refund",
        "category": "billing",
        "priority": "medium",
        "action": "refund",
    },
    {
        "id": "5",
        "query": "The API is returning 500 errors in production for all requests",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
]
