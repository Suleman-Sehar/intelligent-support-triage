#!/usr/bin/env python3
"""
Evaluation script for support ticket triage.
Produces baseline vs AI comparison table and saves evidence.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import argparse


def load_predictions(filepath: str) -> List[dict]:
    """Load predictions from CSV."""
    preds = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            preds.append(row)
    return preds


def load_ground_truth(input_file: str, split: str) -> List[dict]:
    """Load ground truth from tickets.csv for a specific split."""
    truths = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] == split:
                truths.append(row)
    return truths


def compute_metrics(preds: List[dict], truths: List[dict], pred_issue_col: str, pred_team_col: str) -> Dict:
    """Compute macro F1, precision, recall for issue_type and team."""
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
        
        per_class = {}
        f1s = []
        for label in sorted(labels):
            precision = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
            recall = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            per_class[label] = {"precision": precision, "recall": recall, "f1": f1}
            f1s.append(f1)
        
        return {
            "macro_f1": sum(f1s) / len(f1s) if f1s else 0,
            "per_class": per_class
        }
    
    issue_preds = [p[pred_issue_col] for p in preds]
    issue_truths = [t["issue_type"] for t in truths]
    team_preds = [p[pred_team_col] for p in preds]
    team_truths = [t["team"] for t in truths]
    
    issue_metrics = macro_f1(issue_preds, issue_truths)
    team_metrics = macro_f1(team_preds, team_truths)
    
    avg_conf = sum(float(p.get("confidence", 0)) for p in preds) / len(preds) if preds else 0
    
    human_review_rate = 0
    if "human_review" in preds[0]:
        human_review_rate = sum(1 for p in preds if p.get("human_review", "False").lower() == "true") / len(preds)
    
    fallback_rate = 0
    if "fallback_used" in preds[0]:
        fallback_rate = sum(1 for p in preds if p.get("fallback_used", "False").lower() == "true") / len(preds)
    
    pii_rate = 0
    if "pii_redacted" in preds[0]:
        pii_rate = sum(1 for p in preds if p.get("pii_redacted", "False").lower() == "true") / len(preds)
    
    return {
        "issue_type": issue_metrics,
        "team": team_metrics,
        "avg_confidence": avg_conf,
        "human_review_rate": human_review_rate,
        "fallback_rate": fallback_rate,
        "pii_redacted_rate": pii_rate,
        "num_samples": len(preds)
    }


def format_comparison_table(baseline_metrics: Dict, llm_metrics: Dict, guardrail_metrics: Dict) -> str:
    """Format a comparison table as markdown."""
    lines = []
    lines.append("# Model Comparison - Test Split")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Main metrics table
    lines.append("## Overall Metrics")
    lines.append("")
    lines.append("| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) | Guardrails (Fallback) |")
    lines.append("|--------|------------------|-------------------|------------------|----------------------|")
    
    b_issue = baseline_metrics["issue_type"]["macro_f1"]
    b_team = baseline_metrics["team"]["macro_f1"]
    l_issue = llm_metrics["issue_type"]["macro_f1"]
    l_team = llm_metrics["team"]["macro_f1"]
    g_issue = guardrail_metrics["issue_type"]["macro_f1"]
    g_team = guardrail_metrics["team"]["macro_f1"]
    
    lines.append(f"| Issue Type Macro F1 | {b_issue:.4f} | {l_issue:.4f} | {g_issue:.4f} | {baseline_metrics['issue_type']['macro_f1']:.4f} |")
    lines.append(f"| Team Macro F1 | {b_team:.4f} | {l_team:.4f} | {g_team:.4f} | {baseline_metrics['team']['macro_f1']:.4f} |")
    lines.append(f"| Avg Confidence | {baseline_metrics['avg_confidence']:.4f} | {llm_metrics['avg_confidence']:.4f} | {guardrail_metrics['avg_confidence']:.4f} | {baseline_metrics['avg_confidence']:.4f} |")
    lines.append(f"| Human Review Rate | N/A | N/A | {guardrail_metrics['human_review_rate']:.2%} | {baseline_metrics.get('human_review_rate', 0):.2%} |")
    lines.append(f"| Fallback Rate | N/A | N/A | {guardrail_metrics['fallback_rate']:.2%} | N/A |")
    lines.append(f"| PII Redacted Rate | N/A | N/A | {guardrail_metrics['pii_redacted_rate']:.2%} | {baseline_metrics.get('pii_redacted_rate', 0):.2%} |")
    lines.append("")
    
    # Improvement
    lines.append("## Improvement Over Baseline")
    lines.append("")
    issue_improvement = (l_issue - b_issue) * 100
    team_improvement = (l_team - b_team) * 100
    lines.append(f"- Issue Type Macro F1: **{issue_improvement:+.2f}%** ({b_issue:.4f} -> {l_issue:.4f})")
    lines.append(f"- Team Macro F1: **{team_improvement:+.2f}%** ({b_team:.4f} -> {l_team:.4f})")
    lines.append("")
    
    # Per-class breakdown
    lines.append("## Per-Class Issue Type F1")
    lines.append("")
    lines.append("| Class | Baseline | LLM | Guardrails (LLM) |")
    lines.append("|-------|----------|-----|------------------|")
    all_classes = set(baseline_metrics["issue_type"]["per_class"].keys()) | \
                  set(llm_metrics["issue_type"]["per_class"].keys()) | \
                  set(guardrail_metrics["issue_type"]["per_class"].keys())
    for cls in sorted(all_classes):
        b = baseline_metrics["issue_type"]["per_class"].get(cls, {}).get("f1", 0)
        l = llm_metrics["issue_type"]["per_class"].get(cls, {}).get("f1", 0)
        g = guardrail_metrics["issue_type"]["per_class"].get(cls, {}).get("f1", 0)
        lines.append(f"| {cls} | {b:.3f} | {l:.3f} | {g:.3f} |")
    lines.append("")
    
    lines.append("## Per-Class Team F1")
    lines.append("")
    lines.append("| Class | Baseline | LLM | Guardrails (LLM) |")
    lines.append("|-------|----------|-----|------------------|")
    all_classes = set(baseline_metrics["team"]["per_class"].keys()) | \
                  set(llm_metrics["team"]["per_class"].keys()) | \
                  set(guardrail_metrics["team"]["per_class"].keys())
    for cls in sorted(all_classes):
        b = baseline_metrics["team"]["per_class"].get(cls, {}).get("f1", 0)
        l = llm_metrics["team"]["per_class"].get(cls, {}).get("f1", 0)
        g = guardrail_metrics["team"]["per_class"].get(cls, {}).get("f1", 0)
        lines.append(f"| {cls} | {b:.3f} | {l:.3f} | {g:.3f} |")
    lines.append("")
    
    # Acceptance criteria check
    lines.append("## Acceptance Criteria Check")
    lines.append("")
    criteria = [
        ("Baseline Issue F1 >= 0.70", b_issue >= 0.70, f"{b_issue:.4f}"),
        ("Baseline Team F1 >= 0.70", b_team >= 0.70, f"{b_team:.4f}"),
        ("LLM Issue F1 improvement >= 0.10", (l_issue - b_issue) >= 0.10, f"{(l_issue - b_issue):.4f}"),
        ("LLM Team F1 improvement >= 0.10", (l_team - b_team) >= 0.10, f"{(l_team - b_team):.4f}"),
        ("Human review rate <= 15%", guardrail_metrics["human_review_rate"] <= 0.15, f"{guardrail_metrics['human_review_rate']:.2%}"),
        ("PII redaction working", guardrail_metrics["pii_redacted_rate"] > 0, f"{guardrail_metrics['pii_redacted_rate']:.2%}"),
    ]
    lines.append("| Criterion | Pass | Value |")
    lines.append("|-----------|------|-------|")
    for name, passed, value in criteria:
        status = "PASS" if passed else "FAIL"
        lines.append(f"| {name} | {status} | {value} |")
    lines.append("")
    
    return "\n".join(lines)


def save_evidence(evidence_dir: Path, basename: str, content: str, metrics: Dict):
    """Save evidence files."""
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Markdown report
    md_path = evidence_dir / f"{basename}_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # JSON metrics
    json_path = evidence_dir / f"{basename}_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Evidence saved to {md_path} and {json_path}")
    return md_path, json_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare models")
    parser.add_argument("--input", default="data/tickets.csv", help="Input tickets CSV")
    parser.add_argument("--split", default="test", choices=["dev", "test"], help="Split to evaluate")
    parser.add_argument("--baseline", default="evidence/baseline_predictions_test.csv", help="Baseline predictions")
    parser.add_argument("--llm", default="evidence/llm_predictions_test.csv", help="LLM predictions")
    parser.add_argument("--guardrail", default="evidence/guardrail_predictions_test.csv", help="Guardrail predictions")
    parser.add_argument("--guardrail-fallback", default="evidence/guardrail_fallback_test.csv", help="Guardrail fallback predictions")
    parser.add_argument("--output-dir", default="evidence", help="Output directory for evidence")
    parser.add_argument("--name", default="evaluation", help="Base name for evidence files")
    args = parser.parse_args()
    
    # Load ground truth
    truths = load_ground_truth(args.input, args.split)
    print(f"Loaded {len(truths)} ground truth tickets from {args.split} split")
    
    # Load predictions
    baseline_preds = load_predictions(args.baseline)
    llm_preds = load_predictions(args.llm)
    guardrail_preds = load_predictions(args.guardrail)
    guardrail_fallback_preds = load_predictions(args.guardrail_fallback)
    
    print(f"Baseline: {len(baseline_preds)} predictions")
    print(f"LLM: {len(llm_preds)} predictions")
    print(f"Guardrails (LLM): {len(guardrail_preds)} predictions")
    print(f"Guardrails (Fallback): {len(guardrail_fallback_preds)} predictions")
    
    # Compute metrics
    baseline_metrics = compute_metrics(baseline_preds, truths, "pred_issue_type", "pred_team")
    llm_metrics = compute_metrics(llm_preds, truths, "pred_issue_type", "pred_team")
    guardrail_metrics = compute_metrics(guardrail_preds, truths, "pred_issue_type", "pred_team")
    guardrail_fallback_metrics = compute_metrics(guardrail_fallback_preds, truths, "pred_issue_type", "pred_team")
    
    # Add guardrail-specific metrics to baseline for comparison table
    baseline_metrics["human_review_rate"] = guardrail_fallback_metrics["human_review_rate"]
    baseline_metrics["pii_redacted_rate"] = guardrail_fallback_metrics["pii_redacted_rate"]
    
    # Generate comparison table
    comparison = format_comparison_table(baseline_metrics, llm_metrics, guardrail_metrics)
    print("\n" + comparison)
    
    # Save evidence
    all_metrics = {
        "baseline": baseline_metrics,
        "llm": llm_metrics,
        "guardrails_llm": guardrail_metrics,
        "guardrails_fallback": guardrail_fallback_metrics,
        "timestamp": datetime.now().isoformat(),
        "split": args.split
    }
    
    save_evidence(Path(args.output_dir), args.name, comparison, all_metrics)
    
    # Also save a latest symlink/copy
    latest_md = Path(args.output_dir) / f"{args.name}_latest.md"
    latest_json = Path(args.output_dir) / f"{args.name}_latest.json"
    with open(latest_md, "w", encoding="utf-8") as f:
        f.write(comparison)
    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"\nLatest evidence: {latest_md}, {latest_json}")


if __name__ == "__main__":
    main()