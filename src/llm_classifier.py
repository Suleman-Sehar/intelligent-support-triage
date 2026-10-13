#!/usr/bin/env python3
"""
LLM-based classifier for support ticket triage with schema validation, retry, and caching.
Uses OpenAI API with structured output (JSON schema).
"""

import csv
import json
import os
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import argparse

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    exit(1)

from pydantic import BaseModel, Field, ValidationError


# Pydantic model for structured output validation
class TicketClassification(BaseModel):
    issue_type: str = Field(description="Issue type classification", 
                           pattern="^(billing|bug|account access|feature request|how-to|outage)$")
    team: str = Field(description="Team routing",
                     pattern="^(billing|tech support|account security|product)$")
    confidence: float = Field(description="Confidence score 0-1", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief reasoning for classification")


# Cache implementation
class PredictionCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        if self.index_file.exists():
            with open(self.index_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.index, f)
    
    def _make_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def get(self, text: str) -> Optional[TicketClassification]:
        key = self._make_key(text)
        if key in self.index:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    data = json.load(f)
                return TicketClassification(**data)
        return None
    
    def set(self, text: str, prediction: TicketClassification):
        key = self._make_key(text)
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, "w") as f:
            json.dump(prediction.model_dump(), f)
        self.index[key] = True
        self._save_index()


# LLM Classifier with retry logic
class LLMClassifier:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0, 
                 max_retries: int = 3, retry_delay: float = 1.0,
                 cache: Optional[PredictionCache] = None,
                 base_url: Optional[str] = None):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache = cache
        
        # JSON schema for structured output
        self.schema = {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": ["billing", "bug", "account access", "feature request", "how-to", "outage"]
                },
                "team": {
                    "type": "string",
                    "enum": ["billing", "tech support", "account security", "product"]
                },
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reasoning": {"type": "string"}
            },
            "required": ["issue_type", "team", "confidence", "reasoning"],
            "additionalProperties": False
        }
        
        self.system_prompt = """You are a support ticket triage classifier for a SaaS helpdesk.
Classify each ticket by issue_type and team, and provide a confidence score.

Issue types:
- billing: Invoice questions, charge discrepancies, refunds, payments, subscriptions
- bug: Application crashes, errors, broken features, data loss, performance issues
- account access: Password resets, 2FA, lockouts, SSO, API key rotation
- feature request: New feature suggestions, enhancements, integrations
- how-to: Setup guides, configuration help, permissions, migrations
- outage: Service downtime, API errors, slow performance, maintenance

Teams:
- billing: Billing and payment issues
- tech support: Technical bugs, outages, how-to questions
- account security: Account access, authentication, security
- product: Feature requests and product feedback

Return ONLY valid JSON matching the schema. Be concise in reasoning."""
    
    def classify(self, subject: str, body: str) -> TicketClassification:
        combined = f"Subject: {subject}\nBody: {body}"
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(combined)
            if cached:
                return cached
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": combined}
        ]
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_schema", "json_schema": {
                        "name": "ticket_classification",
                        "schema": self.schema,
                        "strict": True
                    }}
                )
                
                content = response.choices[0].message.content
                data = json.loads(content)
                prediction = TicketClassification(**data)
                
                # Cache successful prediction
                if self.cache:
                    self.cache.set(combined, prediction)
                
                return prediction
                
            except ValidationError as e:
                last_error = f"Schema validation failed: {e}"
                print(f"  Attempt {attempt+1}/{self.max_retries}: {last_error}")
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                print(f"  Attempt {attempt+1}/{self.max_retries}: {last_error}")
            except Exception as e:
                last_error = f"API error: {e}"
                print(f"  Attempt {attempt+1}/{self.max_retries}: {last_error}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed - raise error
        raise RuntimeError(f"LLM classification failed after {self.max_retries} retries: {last_error}")


@dataclass
class ClassificationResult:
    issue_type: str
    team: str
    confidence: float
    reasoning: str


def load_tickets(input_file: str, split: str) -> List[dict]:
    tickets = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] == split:
                tickets.append(row)
    return tickets


def evaluate(predictions: List[ClassificationResult], ground_truth: List[dict]) -> dict:
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
    }


def main():
    parser = argparse.ArgumentParser(description="LLM-based ticket classifier")
    parser.add_argument("--input", default="data/tickets.csv", help="Input CSV")
    parser.add_argument("--split", default="dev", choices=["dev", "test"], help="Split to evaluate")
    parser.add_argument("--output", default="evidence/llm_predictions_dev.csv", help="Output predictions")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    parser.add_argument("--base-url", default=None, help="API base URL (e.g., https://openrouter.ai/api/v1 for OpenRouter)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max API retries")
    parser.add_argument("--cache-dir", default="cache", help="Cache directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit tickets for testing")
    args = parser.parse_args()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in environment")
        exit(1)
    
    tickets = load_tickets(args.input, args.split)
    if args.limit:
        tickets = tickets[:args.limit]
    
    print(f"Classifying {len(tickets)} tickets from {args.split} split using {args.model}...")
    
    cache = PredictionCache(args.cache_dir)
    classifier = LLMClassifier(model=args.model, max_retries=args.max_retries, cache=cache, base_url=args.base_url)
    
    predictions = []
    failed = 0
    
    for i, t in enumerate(tickets):
        try:
            result = classifier.classify(t["subject"], t["body"])
            predictions.append(ClassificationResult(
                issue_type=result.issue_type,
                team=result.team,
                confidence=result.confidence,
                reasoning=result.reasoning
            ))
        except Exception as e:
            print(f"  Failed to classify {t['id']}: {e}")
            failed += 1
            # Fallback to low-confidence default
            predictions.append(ClassificationResult(
                issue_type="how-to",
                team="tech support",
                confidence=0.1,
                reasoning="Fallback due to classification failure"
            ))
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(tickets)}")
    
    print(f"\nCompleted: {len(predictions) - failed} succeeded, {failed} failed")
    
    metrics = evaluate(predictions, tickets)
    
    print(f"\nLLM Metrics ({args.split}):")
    print(f"  Issue Type Macro F1: {metrics['issue_type_macro_f1']:.4f}")
    print(f"  Team Macro F1:       {metrics['team_macro_f1']:.4f}")
    print(f"  Avg Confidence:      {metrics['avg_confidence']:.4f}")
    
    # Save predictions
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "pred_issue_type", "pred_team", "confidence", "reasoning", "true_issue_type", "true_team"])
        for t, p in zip(tickets, predictions):
            writer.writerow([t["id"], p.issue_type, p.team, f"{p.confidence:.4f}", p.reasoning, t["issue_type"], t["team"]])
    
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