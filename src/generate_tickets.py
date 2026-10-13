#!/usr/bin/env python3
"""
Synthetic ticket generator for SaaS helpdesk triage.
Produces data/tickets.csv with columns: id, subject, body, issue_type, team, split
"""

import csv
import random
from dataclasses import dataclass
from typing import List
import argparse


@dataclass
class TicketTemplate:
    issue_type: str
    team: str
    subjects: List[str]
    bodies: List[str]


TEMPLATES = [
    # Billing
    TicketTemplate("billing", "billing",
        ["Invoice question", "Charge discrepancy", "Refund request", "Payment failed", "Subscription upgrade"],
        [
            "I was charged $49.99 but my plan shows $29.99. Can you explain the difference?",
            "My credit card was declined but I have sufficient funds. Please retry the payment.",
            "I'd like a refund for the last month since I didn't use the service.",
            "The invoice #INV-2024-001234 shows a different amount than my contract.",
            "How do I upgrade from Pro to Enterprise plan? What's the prorated cost?",
        ]),
    # Bug
    TicketTemplate("bug", "tech support",
        ["Application crash", "Feature not working", "Data loss", "Performance issue", "UI glitch"],
        [
            "The app crashes every time I click 'Export Report'. Error: NullPointerException at line 245.",
            "The 'Save as Draft' button doesn't work - clicks register but nothing saves.",
            "After the latest update, all my custom filters are gone. Need them restored.",
            "Dashboard loads in 15+ seconds. It used to be under 2 seconds.",
            "Text overlaps on the Settings page when using dark mode on mobile.",
        ]),
    # Account Access
    TicketTemplate("account access", "account security",
        ["Password reset", "2FA issues", "Locked out", "SSO configuration", "API key rotation"],
        [
            "I'm not receiving the password reset email. Checked spam folder.",
            "Lost my authenticator app. Need to reset 2FA for account admin@company.com.",
            "Account locked after 5 failed attempts. It wasn't me - possible brute force?",
            "Setting up SAML SSO with Okta. Getting 'Invalid audience' error.",
            "Need to rotate API keys for security compliance. How to do this without downtime?",
        ]),
    # Feature Request
    TicketTemplate("feature request", "product",
        ["Dark mode", "Export formats", "Webhook support", "Custom fields", "Bulk actions"],
        [
            "Please add dark mode toggle. Current light theme causes eye strain.",
            "Need CSV and PDF export options for reports. Currently only JSON.",
            "Webhook notifications for ticket status changes would help our workflow.",
            "Allow custom fields on tickets so we can track internal ticket IDs.",
            "Bulk close/resolve multiple tickets at once. Currently one by one.",
        ]),
    # How-to
    TicketTemplate("how-to", "tech support",
        ["Setup integration", "Configure workflow", "User permissions", "Report building", "Data migration"],
        [
            "How do I connect the Slack integration? Documentation is unclear.",
            "Setting up approval workflow for expense reports. Need step-by-step.",
            "What's the difference between Admin, Manager, and Viewer roles?",
            "How to build a custom report showing tickets by category per month?",
            "Migrating from Zendesk. Best practices for importing historical data?",
        ]),
    # Outage
    TicketTemplate("outage", "tech support",
        ["Service down", "API errors", "Slow response", "Partial outage", "Scheduled maintenance"],
        [
            "Entire platform returning 503 since 14:00 UTC. Any ETA?",
            "API returning 500 errors for /v1/tickets endpoint. Started 10 min ago.",
            "All requests timing out. Dashboard shows 'Connecting...' indefinitely.",
            "EU region users cannot log in. US region works fine.",
            "Is there scheduled maintenance tonight? Our team needs to plan around it.",
        ]),
]


def generate_tickets(num_tickets: int = 1000, seed: int = 42) -> List[dict]:
    random.seed(seed)
    tickets = []
    
    for i in range(num_tickets):
        template = random.choice(TEMPLATES)
        subject = random.choice(template.subjects)
        body = random.choice(template.bodies)
        
        # Add some variation
        if random.random() < 0.3:
            body += f" Ticket ref: #{random.randint(10000, 99999)}"
        if random.random() < 0.2:
            body += f" Contact: user{random.randint(1, 500)}@example.com"
        if random.random() < 0.1:
            body += f" Phone: +1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        # Assign split: 80% dev, 20% test
        split = "dev" if random.random() < 0.8 else "test"
        
        tickets.append({
            "id": f"TKT-{i+1:05d}",
            "subject": subject,
            "body": body,
            "issue_type": template.issue_type,
            "team": template.team,
            "split": split
        })
    
    return tickets


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic support tickets")
    parser.add_argument("-n", "--num", type=int, default=1000, help="Number of tickets")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")
    parser.add_argument("-o", "--output", default="data/tickets.csv", help="Output CSV path")
    args = parser.parse_args()
    
    tickets = generate_tickets(args.num, args.seed)
    
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject", "body", "issue_type", "team", "split"])
        writer.writeheader()
        writer.writerows(tickets)
    
    dev_count = sum(1 for t in tickets if t["split"] == "dev")
    test_count = sum(1 for t in tickets if t["split"] == "test")
    
    print(f"Generated {len(tickets)} tickets -> {args.output}")
    print(f"  Dev: {dev_count} | Test: {test_count}")
    print(f"  Issue types: {len(set(t['issue_type'] for t in tickets))}")
    print(f"  Teams: {len(set(t['team'] for t in tickets))}")


if __name__ == "__main__":
    main()