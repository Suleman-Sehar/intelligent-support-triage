# Model Comparison - Test Split
Generated: 2026-10-13T19:16:23.009315

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
