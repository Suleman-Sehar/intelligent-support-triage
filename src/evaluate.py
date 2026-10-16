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


# Urgency derived from issue type
URGENCY_MAP = {
    "outage": "critical",
    "bug": "high",
    "account access": "high",
    "billing": "medium",
    "feature request": "low",
    "how-to": "low",
}
URGENCY_ORDER = ["critical", "high", "medium", "low"]


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
    
    # Urgency metrics (derived from issue_type)
    urgency_preds = [URGENCY_MAP.get(p.get(pred_issue_col, ""), "low") for p in preds]
    urgency_truths = [URGENCY_MAP.get(t.get("issue_type", ""), "low") for t in truths]
    urgency_metrics = macro_f1(urgency_preds, urgency_truths)
    
    # Guardrail value: auto-routed vs flagged accuracy
    auto_routed_correct = 0
    auto_routed_total = 0
    flagged_correct = 0
    flagged_total = 0
    total_errors = 0
    errors_caught = 0
    
    if "human_review" in preds[0]:
        for p, t in zip(preds, truths):
            is_correct = p.get(pred_issue_col) == t.get("issue_type") and p.get(pred_team_col) == t.get("team")
            if not is_correct:
                total_errors += 1
            flagged = p.get("human_review", "False").lower() == "true"
            if flagged:
                flagged_total += 1
                if not is_correct:
                    errors_caught += 1
                if is_correct:
                    flagged_correct += 1
            else:
                auto_routed_total += 1
                if is_correct:
                    auto_routed_correct += 1
    
    auto_routed_accuracy = auto_routed_correct / auto_routed_total if auto_routed_total > 0 else 0
    flagged_accuracy = flagged_correct / flagged_total if flagged_total > 0 else 0
    errors_caught_rate = errors_caught / total_errors if total_errors > 0 else 0
    
    return {
        "issue_type": issue_metrics,
        "team": team_metrics,
        "urgency": urgency_metrics,
        "avg_confidence": avg_conf,
        "human_review_rate": human_review_rate,
        "fallback_rate": fallback_rate,
        "pii_redacted_rate": pii_rate,
        "num_samples": len(preds),
        "auto_routed_accuracy": auto_routed_accuracy,
        "auto_routed_total": auto_routed_total,
        "flagged_accuracy": flagged_accuracy,
        "flagged_total": flagged_total,
        "total_errors": total_errors,
        "errors_caught": errors_caught,
        "errors_caught_rate": errors_caught_rate,
    }


def format_comparison_table(baseline_metrics: Dict, llm_metrics: Dict, guardrail_metrics: Dict) -> str:
    """Format a comparison table as markdown."""
    lines = []
    lines.append("# Model Comparison - Test Split")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("> Note: Test split = 191 tickets. Small sample size; per-class metrics may have high variance.")
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
    lines.append(f"| Urgency Macro F1 | N/A | {llm_metrics.get('urgency', {}).get('macro_f1', 0):.4f} | {guardrail_metrics.get('urgency', {}).get('macro_f1', 0):.4f} | {baseline_metrics.get('urgency', {}).get('macro_f1', 0):.4f} |")
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
    
    # Urgency metrics (derived from issue type)
    lines.append("## Urgency Metrics")
    lines.append("")
    lines.append("Urgency is derived from issue type: outage=critical, bug/account access=high, billing=medium, feature request/how-to=low.")
    lines.append("")
    lines.append("| Urgency | Baseline P | Baseline R | LLM P | LLM R | Guardrails P | Guardrails R |")
    lines.append("|-------|------------|------------|-------|-------|--------------|--------------|")
    
    b_urg = baseline_metrics.get("urgency", {}).get("per_class", {})
    l_urg = llm_metrics.get("urgency", {}).get("per_class", {})
    g_urg = guardrail_metrics.get("urgency", {}).get("per_class", {})
    
    for urg in URGENCY_ORDER:
        b = b_urg.get(urg, {"precision": 0, "recall": 0, "f1": 0})
        l = l_urg.get(urg, {"precision": 0, "recall": 0, "f1": 0})
        g = g_urg.get(urg, {"precision": 0, "recall": 0, "f1": 0})
        lines.append(f"| {urg} | {b['precision']:.3f} | {b['recall']:.3f} | {l['precision']:.3f} | {l['recall']:.3f} | {g['precision']:.3f} | {g['recall']:.3f} |")
    
    lines.append(f"| **Macro F1** | | | **{llm_metrics.get('urgency', {}).get('macro_f1', 0):.4f}** | | | |")
    lines.append("")
    
    # Guardrail value section
    lines.append("## Guardrail Value")
    lines.append("")
    g_ar = guardrail_metrics.get("auto_routed_accuracy", 0)
    g_ar_n = guardrail_metrics.get("auto_routed_total", 0)
    g_fa = guardrail_metrics.get("flagged_accuracy", 0)
    g_fn = guardrail_metrics.get("flagged_total", 0)
    g_ec = guardrail_metrics.get("errors_caught_rate", 0)
    g_ec_n = guardrail_metrics.get("errors_caught", 0)
    g_te = guardrail_metrics.get("total_errors", 0)
    
    lines.append(f"- Auto-routed accuracy ({g_ar_n} tickets, human_review=False): {g_ar:.2%}")
    lines.append(f"- Flagged accuracy ({g_fn} tickets, human_review=True): {g_fa:.2%}")
    lines.append(f"- Share of all errors caught by guardrails: {g_ec:.2%} ({g_ec_n} of {g_te} errors)")
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


def compute_per_slice_metrics(preds: List[dict], truths: List[dict]) -> Dict:
    """Compute metrics for easy/hard/edge-case slices."""
    from collections import defaultdict
    
    def macro_f1(pred_labels, true_labels):
        labels = set(true_labels)
        tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
        for p, t in zip(pred_labels, true_labels):
            if p == t: tp[p] += 1
            else:
                fp[p] += 1; fn[t] += 1
        f1s = []
        for label in labels:
            prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
            rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
            f1s.append(f1)
        return sum(f1s) / len(f1s) if f1s else 0
    
    # Slice by confidence: easy (>=0.9), hard (<0.75), edge (0.75-0.9)
    easy = []
    hard = []
    edge = []
    
    for p, t in zip(preds, truths):
        conf = float(p.get("confidence", 0.9))
        if conf >= 0.9:
            easy.append((p, t))
        elif conf < 0.75:
            hard.append((p, t))
        else:
            edge.append((p, t))
    
    slices = {}
    for name, items in [("easy (conf>=0.9)", easy), ("hard (conf<0.75)", hard), ("edge (0.75-0.9)", edge)]:
        if items:
            p_items = [i[0] for i in items]
            t_items = [i[1] for i in items]
            slices[name] = {
                "issue_type_f1": macro_f1([p["pred_issue_type"] for p in p_items], [t["issue_type"] for t in t_items]),
                "team_f1": macro_f1([p["pred_team"] for p in p_items], [t["team"] for t in t_items]),
                "count": len(items)
            }
        else:
            slices[name] = {"issue_type_f1": 0, "team_f1": 0, "count": 0}
    
    return slices


def format_per_slice_table(baseline_preds: List[dict], llm_preds: List[dict], truths: List[dict]) -> str:
    """Format per-slice comparison table."""
    lines = []
    lines.append("## How to Read This Report")
    lines.append("")
    lines.append("- **Overall Metrics**: Aggregate across 191 test tickets.")
    lines.append("- **Per-Class F1**: Identifies weak classes")
    lines.append("- **Per-Slice Results**: Tickets grouped by confidence band")
    lines.append("  - *easy (conf>=0.9)*: High-confidence; both models should excel")
    lines.append("  - *edge (0.75-0.9)*: Medium-confidence; where LLM should outperform rules")
    lines.append("  - *hard (conf<0.75)*: Low-confidence; flagged for human review")
    lines.append("- Small sample size (191) limits statistical significance")
    lines.append("")
    lines.append("## Per-Slice Results (Confidence-based)")
    lines.append("")
    lines.append("| Slice | Count | Baseline Issue F1 | LLM Issue F1 | Baseline Team F1 | LLM Team F1 |")
    lines.append("|-------|-------|-------------------|--------------|------------------|-------------|")
    
    baseline_slices = compute_per_slice_metrics(baseline_preds, truths)
    llm_slices = compute_per_slice_metrics(llm_preds, truths)
    
    for slice_name in ["easy (conf>=0.9)", "edge (0.75-0.9)", "hard (conf<0.75)"]:
        b = baseline_slices.get(slice_name, {"count": 0, "issue_type_f1": 0, "team_f1": 0})
        l = llm_slices.get(slice_name, {"count": 0, "issue_type_f1": 0, "team_f1": 0})
        count = b["count"] if b["count"] > 0 else l["count"]
        lines.append(f"| {slice_name} | {count} | {b['issue_type_f1']:.3f} | {l['issue_type_f1']:.3f} | {b['team_f1']:.3f} | {l['team_f1']:.3f} |")
    
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
    
    # Per-slice results
    slice_table = format_per_slice_table(baseline_preds, llm_preds, truths)
    print(slice_table)
    
    # Save evidence
    all_metrics = {
        "baseline": baseline_metrics,
        "llm": llm_metrics,
        "guardrails_llm": guardrail_metrics,
        "guardrails_fallback": guardrail_fallback_metrics,
        "timestamp": datetime.now().isoformat(),
        "split": args.split,
        "test_set_size": len(truths),
        "per_slice": {
            "baseline": compute_per_slice_metrics(baseline_preds, truths),
            "llm": compute_per_slice_metrics(llm_preds, truths)
        }
    }
    
    full_comparison = comparison + "\n" + slice_table
    
    save_evidence(Path(args.output_dir), args.name, full_comparison, all_metrics)
    
    # Also save a latest copy
    latest_md = Path(args.output_dir) / f"{args.name}_latest.md"
    latest_json = Path(args.output_dir) / f"{args.name}_latest.json"
    with open(latest_md, "w", encoding="utf-8") as f:
        f.write(full_comparison)
    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"\nLatest evidence: {latest_md}, {latest_json}")


if __name__ == "__main__":
    main()