# Model Comparison - Test Split
Generated: 2026-10-14T11:25:04.838608

> Note: Test split = 191 tickets (~30 per class). Small sample size; per-class metrics may have high variance.

## Overall Metrics

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) | Guardrails (Fallback) |
|--------|------------------|-------------------|------------------|----------------------|
| Issue Type Macro F1 | 0.9683 | 0.9838 | 0.9838 | 0.9683 |
| Team Macro F1 | 0.9228 | 0.9830 | 0.9830 | 0.9228 |
| Avg Confidence | 0.8662 | 0.9411 | 0.9411 | 0.8662 |
| Human Review Rate | N/A | N/A | 0.00% | 10.99% |
| Fallback Rate | N/A | N/A | 0.00% | N/A |
| PII Redacted Rate | N/A | N/A | 26.70% | 26.70% |

## Improvement Over Baseline

- Issue Type Macro F1: **+1.54%** (0.9683 -> 0.9838)
- Team Macro F1: **+6.02%** (0.9228 -> 0.9830)

## Per-Class Issue Type F1

| Class | Baseline | LLM | Guardrails (LLM) |
|-------|----------|-----|------------------|
| account access | 1.000 | 0.947 | 0.947 |
| billing | 1.000 | 1.000 | 1.000 |
| bug | 0.941 | 1.000 | 1.000 |
| feature request | 0.972 | 1.000 | 1.000 |
| how-to | 0.897 | 0.955 | 0.955 |
| outage | 1.000 | 1.000 | 1.000 |

## Per-Class Team F1

| Class | Baseline | LLM | Guardrails (LLM) |
|-------|----------|-----|------------------|
| account security | 1.000 | 0.947 | 0.947 |
| billing | 0.967 | 1.000 | 1.000 |
| product | 0.793 | 1.000 | 1.000 |
| tech support | 0.931 | 0.985 | 0.985 |

## Acceptance Criteria Check

| Criterion | Pass | Value |
|-----------|------|-------|
| Baseline Issue F1 >= 0.70 | PASS | 0.9683 |
| Baseline Team F1 >= 0.70 | PASS | 0.9228 |
| LLM Issue F1 improvement >= 0.10 | FAIL | 0.0154 |
| LLM Team F1 improvement >= 0.10 | FAIL | 0.0602 |
| Human review rate <= 15% | PASS | 0.00% |
| PII redaction working | PASS | 26.70% |

## Per-Slice Results (Confidence-based)

| Slice | Count | Baseline Issue F1 | LLM Issue F1 | Baseline Team F1 | LLM Team F1 |
|-------|-------|-------------------|--------------|------------------|-------------|
| easy (conf>=0.9) | 112 | 1.000 | 0.986 | 1.000 | 0.984 |
| edge (0.75-0.9) | 58 | 0.964 | 0.937 | 0.839 | 0.945 |
| hard (conf<0.75) | 21 | 0.845 | 0.000 | 0.846 | 0.000 |
