# Model Comparison - Test Split
Generated: 2026-10-16T15:10:30.767734

> Note: Test split = 191 tickets. Small sample size; per-class metrics may have high variance.

## Overall Metrics

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) | Guardrails (Fallback) |
|--------|------------------|-------------------|------------------|----------------------|
| Issue Type Macro F1 | 0.9683 | 0.9838 | 0.9838 | 0.9683 |
| Team Macro F1 | 0.9228 | 0.9830 | 0.9830 | 0.9228 |
| Avg Confidence | 0.8662 | 0.9411 | 0.9421 | 0.8662 |
| Human Review Rate | N/A | N/A | 6.81% | 10.99% |
| Fallback Rate | N/A | N/A | 0.00% | N/A |
| PII Redacted Rate | N/A | N/A | 26.70% | 26.70% |
| Urgency Macro F1 | N/A | 0.9883 | 0.9883 | 0.9845 |

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

## Urgency Metrics

Urgency is derived from issue type: outage=critical, bug/account access=high, billing=medium, feature request/how-to=low.

| Urgency | Baseline P | Baseline R | LLM P | LLM R | Guardrails P | Guardrails R |
|-------|------------|------------|-------|-------|--------------|--------------|
| critical | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| high | 0.939 | 1.000 | 1.000 | 0.952 | 1.000 | 0.952 |
| medium | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| low | 1.000 | 0.940 | 0.957 | 1.000 | 0.957 | 1.000 |
| **Macro F1** | | | **0.9883** | | | |

## Guardrail Value

- Auto-routed accuracy (178 tickets, human_review=False): 100.00%
- Flagged accuracy (13 tickets, human_review=True): 76.92%
- Share of all errors caught by guardrails: 100.00% (3 of 3 errors)

## Acceptance Criteria Check

| Criterion | Pass | Value |
|-----------|------|-------|
| Baseline Issue F1 >= 0.70 | PASS | 0.9683 |
| Baseline Team F1 >= 0.70 | PASS | 0.9228 |
| LLM Issue F1 improvement >= 0.10 | FAIL | 0.0154 |
| LLM Team F1 improvement >= 0.10 | FAIL | 0.0602 |
| Human review rate <= 15% | PASS | 6.81% |
| PII redaction working | PASS | 26.70% |

## How to Read This Report

- **Overall Metrics**: Aggregate across 191 test tickets.
- **Per-Class F1**: Identifies weak classes
- **Per-Slice Results**: Tickets grouped by confidence band
  - *easy (conf>=0.9)*: High-confidence; both models should excel
  - *edge (0.75-0.9)*: Medium-confidence; where LLM should outperform rules
  - *hard (conf<0.75)*: Low-confidence; flagged for human review
- Small sample size (191) limits statistical significance

## Per-Slice Results (Confidence-based)

| Slice | Count | Baseline Issue F1 | LLM Issue F1 | Baseline Team F1 | LLM Team F1 |
|-------|-------|-------------------|--------------|------------------|-------------|
| easy (conf>=0.9) | 112 | 1.000 | 0.986 | 1.000 | 0.984 |
| edge (0.75-0.9) | 58 | 0.964 | 0.937 | 0.839 | 0.945 |
| hard (conf<0.75) | 21 | 0.845 | 0.000 | 0.846 | 0.000 |
## Challenge Set Results

Challenge set: 39 hand-labeled tickets (paraphrased, noisy, multi-issue, Roman-Urdu, ambiguous). Not used for tuning.

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) |
|--------|------------------|-------------------|------------------|
| Issue Type Macro F1 | 0.7699 | 0.8382 | 0.8382 |
| Team Macro F1 | 0.8241 | 0.8249 | 0.8249 |
| Avg Confidence | 0.7469 | 0.9090 | 0.9090 |

### Per-Class Issue Type F1 (Challenge)

| Class | Baseline | LLM | Guardrails |
|-------|----------|-----|------------|
| account access | 1.000 | 0.600 | 0.600 |
| billing | 0.933 | 1.000 | 1.000 |
| bug | 0.444 | 0.833 | 0.833 |
| feature request | 0.727 | 0.909 | 0.909 |
| how-to | 0.714 | 0.778 | 0.778 |
| outage | 0.800 | 0.909 | 0.909 |
