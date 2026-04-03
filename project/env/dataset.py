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
    {
        "id": "6",
        "query": "I was charged twice for last month and need one payment reversed",
        "category": "billing",
        "priority": "high",
        "action": "refund",
    },
    {
        "id": "7",
        "query": "We need to add a second admin to our workspace but cannot find the setting",
        "category": "account",
        "priority": "medium",
        "action": "guide",
    },
    {
        "id": "8",
        "query": "SSO login fails with invalid assertion for all employees since this morning",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "9",
        "query": "Please downgrade us to the starter tier from next billing cycle",
        "category": "billing",
        "priority": "medium",
        "action": "guide",
    },
    {
        "id": "10",
        "query": "Our finance team needs VAT invoices for Q1; where can we download them?",
        "category": "billing",
        "priority": "low",
        "action": "guide",
    },
    {
        "id": "11",
        "query": "I cannot delete a former employee account and they still appear in permissions",
        "category": "account",
        "priority": "medium",
        "action": "escalate",
    },
    {
        "id": "12",
        "query": "Webhook deliveries are timing out and orders are not syncing to our ERP",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "13",
        "query": "After updating payment details, our users also cannot sign in through SSO and invoices are missing.",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "14",
        "query": "We got a duplicate charge and now the owner account is locked out after too many reset attempts.",
        "category": "account",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "15",
        "query": "Need immediate invoice correction; meanwhile data export button disappeared after this morning release.",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
    {
        "id": "16",
        "query": "Please cancel subscription at renewal, but right now payroll sync is failing and staff cannot clock in.",
        "category": "technical",
        "priority": "high",
        "action": "escalate",
    },
]
