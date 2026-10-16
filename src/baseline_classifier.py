#!/usr/bin/env python3
"""
Rules-based baseline classifier for support ticket triage.
Uses keyword matching to classify issue_type and team.
"""

import csv
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
import argparse


@dataclass
class ClassificationResult:
    issue_type: str
    team: str
    confidence: float
    urgency: str = "low"


# Keyword rules for urgency classification (text-based signals, built on dev split only)
# Priority order: critical > high > medium > low. First match wins.
URGENCY_KEYWORDS = {
    "critical": [
        "down", "outage", "all users", "entire platform", "everyone",
        "critical", "emergency", "completely down", "site is down",
        "whole site", "all users can't", "all users cannot",
    ],
    "high": [
        "urgent", "asap", "immediately", "cannot log in", "locked out",
        "data loss", "crash", "broken", "error", "failed", "failure",
        "not working", "doesn't work",
    ],
    "medium": [
        "charged twice", "billing", "invoice", "payment", "refund",
        "subscription", "charge", "overcharged",
    ],
    "low": [
        "how to", "how do i", "feature", "request", "question",
        "guide", "setup", "configure", "documentation", "tutorial",
    ],
}

# Fallback: issue type -> urgency
ISSUE_TYPE_TO_URGENCY = {
    "outage": "critical",
    "bug": "high",
    "account access": "high",
    "billing": "medium",
    "feature request": "low",
    "how-to": "low",
}

URGENCY_ORDER = ["critical", "high", "medium", "low"]


# Keyword rules for issue type classification
ISSUE_TYPE_KEYWORDS = {
    "billing": [
        "invoice", "charge", "refund", "payment", "subscription", "billing", "price",
        "cost", "prorated", "upgrade", "downgrade", "plan", "fee", "credit card",
        "receipt", "transaction", "billing cycle"
    ],
    "bug": [
        "crash", "error", "bug", "exception", "fail", "broken", "not working",
        "doesn't work", "glitch", "issue", "problem", "defect", "broken",
        "nullpointer", "timeout", "data loss", "missing", "gone"
    ],
    "account access": [
        "password", "reset", "2fa", "two-factor", "authenticator", "locked",
        "lockout", "sso", "saml", "okta", "login", "sign in", "access",
        "api key", "rotate", "credential", "authentication"
    ],
    "feature request": [
        "feature", "request", "add", "please add", "would like", "suggest",
        "enhancement", "improvement", "dark mode", "export", "webhook",
        "custom field", "bulk", "integration", "notification"
    ],
    "how-to": [
        "how to", "how do i", "setup", "configure", "setting up", "guide",
        "tutorial", "documentation", "steps", "instruction", "best practice",
        "migrate", "import", "connect", "difference between", "what is"
    ],
    "outage": [
        "down", "outage", "500", "503", "502", "504", "timeout", "unavailable",
        "not responding", "slow", "latency", "maintenance", "scheduled",
        "region", "api error", "service down", "platform"
    ],
}

# Keyword rules for team classification
TEAM_KEYWORDS = {
    "billing": [
        "invoice", "charge", "refund", "payment", "subscription", "billing",
        "price", "cost", "prorated", "upgrade", "downgrade", "plan", "fee",
        "credit card", "receipt", "transaction"
    ],
    "tech support": [
        "crash", "error", "bug", "exception", "fail", "broken", "not working",
        "doesn't work", "glitch", "issue", "problem", "defect", "timeout",
        "data loss", "performance", "slow", "dashboard", "ui", "mobile",
        "dark mode", "export", "save", "filter", "slack", "integration",
        "workflow", "report", "permission", "role", "migrate", "import",
        "down", "outage", "500", "503", "unavailable", "not responding",
        "latency", "maintenance", "api error", "service", "platform"
    ],
    "account security": [
        "password", "reset", "2fa", "two-factor", "authenticator", "locked",
        "lockout", "sso", "saml", "okta", "login", "sign in", "access",
        "api key", "rotate", "credential", "authentication", "security"
    ],
    "product": [
        "feature", "request", "add", "please add", "would like", "suggest",
        "enhancement", "improvement", "dark mode", "export", "webhook",
        "custom field", "bulk", "notification"
    ],
}


def classify_text(text: str, keyword_map: Dict[str, List[str]]) -> Tuple[str, float]:
    """Classify text using keyword matching. Returns (label, confidence)."""
    text_lower = text.lower()
    scores = {}
    
    for label, keywords in keyword_map.items():
        score = 0
        for kw in keywords:
            # Count occurrences
            count = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
            score += count
        scores[label] = score
    
    if not scores or max(scores.values()) == 0:
        # Default fallback
        default_label = max(keyword_map.keys(), key=lambda k: len(keyword_map[k]))
        return default_label, 0.1
    
    best_label = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best_label] / total if total > 0 else 0.1
    
    # Boost confidence slightly for better separation
    confidence = min(0.95, confidence + 0.15)
    
    return best_label, confidence


def classify_urgency(text: str, issue_type: str) -> str:
    """Classify urgency using keyword rules with issue-type fallback."""
    text_lower = text.lower()
    
    # Priority order: critical > high > medium > low
    for urgency in URGENCY_ORDER:
        for kw in URGENCY_KEYWORDS[urgency]:
            if kw in text_lower:
                return urgency
    
    # Fallback: derive from predicted issue type
    return ISSUE_TYPE_TO_URGENCY.get(issue_type, "low")


def classify_ticket(subject: str, body: str) -> ClassificationResult:
    """Classify a single ticket by issue type, team, and urgency."""
    combined = f"{subject} {body}"
    
    issue_type, issue_conf = classify_text(combined, ISSUE_TYPE_KEYWORDS)
    team, team_conf = classify_text(combined, TEAM_KEYWORDS)
    
    # Overall confidence is geometric mean
    confidence = (issue_conf * team_conf) ** 0.5
    
    urgency = classify_urgency(combined, issue_type)
    
    return ClassificationResult(issue_type=issue_type, team=team, confidence=confidence, urgency=urgency)


def evaluate(predictions: List[ClassificationResult], ground_truth: List[dict]) -> dict:
    """Compute macro F1 for issue_type and team."""
    from collections import defaultdict
    
    def macro_f1(pred_labels, true_labels):
        labels = set(true_labels)
        tp = defaultdict(int)
        fp = defaultdict(int)
        fn = defaultdict(int)
        
        for p_label, t_label in zip(pred_labels, true_labels):
            if p_label == t_label:
                tp[p_label] += 1
            else:
                fp[p_label] += 1
                fn[t_label] += 1
        
        f1s = []
        for label in labels:
            precision = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
            recall = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            f1s.append(f1)
        
        return sum(f1s) / len(f1s) if f1s else 0
    
    issue_preds = [p.issue_type for p in predictions]
    issue_truths = [t["issue_type"] for t in ground_truth]
    team_preds = [p.team for p in predictions]
    team_truths = [t["team"] for t in ground_truth]
    urgency_preds = [p.urgency for p in predictions]
    urgency_truths = [ISSUE_TYPE_TO_URGENCY.get(t["issue_type"], "low") for t in ground_truth]
    
    return {
        "issue_type_macro_f1": macro_f1(issue_preds, issue_truths),
        "team_macro_f1": macro_f1(team_preds, team_truths),
        "urgency_macro_f1": macro_f1(urgency_preds, urgency_truths),
        "urgency_per_class": _urgency_per_class(urgency_preds, urgency_truths),
        "avg_confidence": sum(p.confidence for p in predictions) / len(predictions),
    }


def _urgency_per_class(pred_labels, true_labels):
    from collections import defaultdict
    tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
    for p_label, t_label in zip(pred_labels, true_labels):
        if p_label == t_label:
            tp[p_label] += 1
        else:
            fp[p_label] += 1
            fn[t_label] += 1
    labels = set(true_labels)
    result = {}
    for label in sorted(labels):
        prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
        rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        result[label] = {"precision": prec, "recall": rec, "f1": f1}
    return result


def main():
    parser = argparse.ArgumentParser(description="Rules-based baseline classifier")
    parser.add_argument("--input", default="data/tickets.csv", help="Input CSV")
    parser.add_argument("--split", default="dev", choices=["dev", "test", "challenge"], help="Split to evaluate")
    parser.add_argument("--output", default="evidence/baseline_predictions.csv", help="Output predictions")
    args = parser.parse_args()
    
    # Load data
    tickets = []
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] == args.split:
                tickets.append(row)
    
    print(f"Evaluating on {args.split} split: {len(tickets)} tickets")
    
    # Classify
    predictions = []
    for t in tickets:
        result = classify_ticket(t["subject"], t["body"])
        predictions.append(result)
    
    # Evaluate
    metrics = evaluate(predictions, tickets)
    
    print(f"\nBaseline Metrics ({args.split}):")
    print(f"  Issue Type Macro F1: {metrics['issue_type_macro_f1']:.4f}")
    print(f"  Team Macro F1:       {metrics['team_macro_f1']:.4f}")
    print(f"  Urgency Macro F1:    {metrics['urgency_macro_f1']:.4f}")
    print(f"  Avg Confidence:      {metrics['avg_confidence']:.4f}")
    
    # Save predictions
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "pred_issue_type", "pred_team", "confidence", "urgency", "true_issue_type", "true_team"])
        for t, p in zip(tickets, predictions):
            writer.writerow([t["id"], p.issue_type, p.team, f"{p.confidence:.4f}", p.urgency, t["issue_type"], t["team"]])
    
    print(f"\nPredictions saved to {args.output}")
    
    # Per-class breakdown
    print("\nPer-class Issue Type F1:")
    from collections import defaultdict
    labels = set(t["issue_type"] for t in tickets)
    tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
    for p, t in zip(predictions, tickets):
        if p.issue_type == t["issue_type"]:
            tp[p.issue_type] += 1
        else:
            fp[p.issue_type] += 1
            fn[t["issue_type"]] += 1
    for label in sorted(labels):
        prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
        rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        print(f"  {label:20s} F1={f1:.3f} (P={prec:.3f}, R={rec:.3f})")
    
    print("\nPer-class Team F1:")
    labels = set(t["team"] for t in tickets)
    tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
    for p, t in zip(predictions, tickets):
        if p.team == t["team"]:
            tp[p.team] += 1
        else:
            fp[p.team] += 1
            fn[t["team"]] += 1
    for label in sorted(labels):
        prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
        rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        print(f"  {label:20s} F1={f1:.3f} (P={prec:.3f}, R={rec:.3f})")

    print("\nPer-class Urgency F1:")
    for label in sorted(metrics["urgency_per_class"].keys()):
        m = metrics["urgency_per_class"][label]
        print(f"  {label:20s} F1={m['f1']:.3f} (P={m['precision']:.3f}, R={m['recall']:.3f})")


if __name__ == "__main__":
    main()