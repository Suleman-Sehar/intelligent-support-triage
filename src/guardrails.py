#!/usr/bin/env python3
"""
Guardrails for support ticket triage:
- PII redaction
- Confidence threshold for human review
- Fallback to rules classifier
"""

import re
import csv
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
import argparse

# Import baseline classifier for fallback
import sys
sys.path.insert(0, str(Path(__file__).parent))
from baseline_classifier import classify_ticket as baseline_classify, ClassificationResult as BaselineResult


@dataclass
class GuardrailResult:
    issue_type: str
    team: str
    confidence: float
    reasoning: str
    pii_redacted: bool
    human_review: bool
    fallback_used: bool
    original_text: str
    redacted_text: str


# PII patterns
PII_PATTERNS = [
    # Email addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # Phone numbers (various formats)
    (r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),
    # API keys (common patterns)
    (r'\b(sk|pk|rk)_[a-zA-Z0-9_]{20,}\b', '[API_KEY]'),
    (r'\b[A-Za-z0-9]{32,}\b', '[API_KEY]'),  # Generic long alphanumeric
    # Credit card numbers (basic pattern)
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD]'),
    # SSN
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    # IP addresses
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
]


def redact_pii(text: str) -> Tuple[str, bool]:
    """Redact PII from text. Returns (redacted_text, was_redacted)."""
    redacted = text
    was_redacted = False
    
    for pattern, replacement in PII_PATTERNS:
        new_text, count = re.subn(pattern, replacement, redacted)
        if count > 0:
            was_redacted = True
        redacted = new_text
    
    return redacted, was_redacted


class GuardrailPipeline:
    def __init__(self, confidence_threshold: float = 0.75, 
                 llm_classifier=None, use_llm: bool = True):
        self.confidence_threshold = confidence_threshold
        self.llm_classifier = llm_classifier
        self.use_llm = use_llm and llm_classifier is not None
    
    def classify_with_guardrails(self, subject: str, body: str) -> GuardrailResult:
        """Classify ticket with all guardrails applied."""
        combined = f"{subject} {body}"
        
        # Step 1: PII redaction
        redacted_text, pii_redacted = redact_pii(combined)
        
        # Step 2: Try LLM classification first
        fallback_used = False
        human_review = False
        
        if self.use_llm:
            try:
                result = self.llm_classifier.classify(subject, body)
                issue_type = result.issue_type
                team = result.team
                confidence = result.confidence
                reasoning = result.reasoning
            except Exception as e:
                print(f"  LLM failed, falling back to rules: {e}")
                fallback_used = True
                baseline_result = baseline_classify(subject, body)
                issue_type = baseline_result.issue_type
                team = baseline_result.team
                confidence = baseline_result.confidence
                reasoning = "Fallback to rules classifier"
        else:
            # Use baseline directly
            baseline_result = baseline_classify(subject, body)
            issue_type = baseline_result.issue_type
            team = baseline_result.team
            confidence = baseline_result.confidence
            reasoning = "Rules classifier (LLM disabled)"
        
        # Step 3: Confidence threshold check
        if confidence < self.confidence_threshold:
            human_review = True
            reasoning += f" | Low confidence ({confidence:.2f} < {self.confidence_threshold}) - flagged for human review"
        
        return GuardrailResult(
            issue_type=issue_type,
            team=team,
            confidence=confidence,
            reasoning=reasoning,
            pii_redacted=pii_redacted,
            human_review=human_review,
            fallback_used=fallback_used,
            original_text=combined,
            redacted_text=redacted_text
        )


def load_tickets(input_file: str, split: str) -> List[dict]:
    tickets = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] == split:
                tickets.append(row)
    return tickets


def evaluate(predictions: List[GuardrailResult], ground_truth: List[dict]) -> dict:
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
    
    return {
        "issue_type_macro_f1": macro_f1(issue_preds, issue_truths),
        "team_macro_f1": macro_f1(team_preds, team_truths),
        "avg_confidence": sum(p.confidence for p in predictions) / len(predictions),
        "human_review_rate": sum(1 for p in predictions if p.human_review) / len(predictions),
        "fallback_rate": sum(1 for p in predictions if p.fallback_used) / len(predictions),
        "pii_redacted_rate": sum(1 for p in predictions if p.pii_redacted) / len(predictions),
    }


def main():
    parser = argparse.ArgumentParser(description="Guardrail pipeline for ticket triage")
    parser.add_argument("--input", default="data/tickets.csv", help="Input CSV")
    parser.add_argument("--split", default="test", choices=["dev", "test"], help="Split to evaluate")
    parser.add_argument("--output", default="evidence/guardrail_predictions_test.csv", help="Output predictions")
    parser.add_argument("--threshold", type=float, default=0.75, help="Confidence threshold for human review")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM, use rules only")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    parser.add_argument("--base-url", default="https://openrouter.ai/api/v1", help="API base URL")
    parser.add_argument("--limit", type=int, default=None, help="Limit tickets for testing")
    args = parser.parse_args()
    
    # Load LLM classifier if available and not disabled
    llm_classifier = None
    if not args.no_llm:
        try:
            from llm_classifier import LLMClassifier, PredictionCache
            cache = PredictionCache("cache")
            llm_classifier = LLMClassifier(
                model=args.model, 
                base_url=args.base_url,
                cache=cache
            )
            print("LLM classifier loaded")
        except Exception as e:
            print(f"Warning: Could not load LLM classifier: {e}")
            print("Falling back to rules-only mode")
    
    tickets = load_tickets(args.input, args.split)
    if args.limit:
        tickets = tickets[:args.limit]
    
    print(f"Processing {len(tickets)} tickets from {args.split} split...")
    print(f"Confidence threshold: {args.threshold}")
    print(f"LLM enabled: {not args.no_llm and llm_classifier is not None}")
    
    pipeline = GuardrailPipeline(
        confidence_threshold=args.threshold,
        llm_classifier=llm_classifier,
        use_llm=not args.no_llm
    )
    
    predictions = []
    for i, t in enumerate(tickets):
        result = pipeline.classify_with_guardrails(t["subject"], t["body"])
        predictions.append(result)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(tickets)}")
    
    metrics = evaluate(predictions, tickets)
    
    print(f"\nGuardrail Metrics ({args.split}):")
    print(f"  Issue Type Macro F1: {metrics['issue_type_macro_f1']:.4f}")
    print(f"  Team Macro F1:       {metrics['team_macro_f1']:.4f}")
    print(f"  Avg Confidence:      {metrics['avg_confidence']:.4f}")
    print(f"  Human Review Rate:   {metrics['human_review_rate']:.2%}")
    print(f"  Fallback Rate:       {metrics['fallback_rate']:.2%}")
    print(f"  PII Redacted Rate:   {metrics['pii_redacted_rate']:.2%}")
    
    # Save predictions
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "pred_issue_type", "pred_team", "confidence", "reasoning",
            "pii_redacted", "human_review", "fallback_used",
            "true_issue_type", "true_team"
        ])
        for t, p in zip(tickets, predictions):
            writer.writerow([
                t["id"], p.issue_type, p.team, f"{p.confidence:.4f}", p.reasoning,
                p.pii_redacted, p.human_review, p.fallback_used,
                t["issue_type"], t["team"]
            ])
    
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


if __name__ == "__main__":
    main()