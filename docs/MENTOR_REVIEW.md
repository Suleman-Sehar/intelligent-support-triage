# Mentor Review Package

**Repo:** https://github.com/Suleman-Sehar/intelligent-support-triage.git  
**Branch:** master  
**Last commit:** 7f73da0 Add sample-size caveats to error_analysis.md

## 5-Line Summary

1. Intelligent Support Triage: a rules-based baseline + LLM (gpt-4o-mini via OpenRouter) classifier with PII guardrails and human-in-the-loop review for SaaS helpdesk tickets.
2. Synthetic test data (seed 42, 191 test tickets) reproduces identically on fresh clone; all 17 unit tests pass.
3. LLM beats baseline on synthetic data: Issue F1 0.9838 vs 0.9683 (+1.6 points), Team F1 0.9830 vs 0.9228 (+6.0 points) — below the 0.10-point acceptance target because synthetic data is near-ceiling for both.
4. On the author-written challenge set (39 noisy/paraphrased/Roman-Urdu tickets), LLM gains +6.8 points on Issue F1 (0.770 → 0.838), confirming real-world noise widens the LLM advantage. Team F1 is flat (0.824 → 0.825, +0.1 points) due to account-security misrouting on Roman-Urdu tickets.
5. Guardrails catch 100% of test-split errors (3 of 3), auto-routed tickets are 100% accurate, PII is redacted before any classifier sees the text, and human review rate is 6.81% (≤15% target).

## Results Table

### Test Split (191 tickets, synthetic)

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) | Guardrails (Fallback) |
|--------|------------------|-------------------|------------------|----------------------|
| Issue Type Macro F1 | 0.9683 | 0.9838 | 0.9838 | 0.9683 |
| Team Macro F1 | 0.9228 | 0.9830 | 0.9830 | 0.9228 |
| Urgency Macro F1 | 0.8562 | 0.9883 | 0.9883 | 0.8562 |
| High/Critical Urgency Recall | 80.00% | 96.84% | 96.84% | 80.00% |
| Human Review Rate | N/A | N/A | 6.81% | 10.99% |
| PII Redacted Rate | N/A | N/A | 26.70% | 26.70% |

### Challenge Set (39 tickets, author-written, AI-assisted, not tuned)

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Guardrails (LLM) |
|--------|------------------|-------------------|------------------|
| Issue Type Macro F1 | 0.7699 | 0.8382 | 0.8382 |
| Team Macro F1 | 0.8241 | 0.8249 | 0.8249 |

## Known Limitations

1. **Unmet 10-point improvement target**: LLM improvement on synthetic data is +1.6 points (Issue) and +6.0 points (Team), below the 0.10-point (10-point) target in requirements.md. Root cause: synthetic ticket templates have clear keyword signals that both rules and LLM classify near-perfectly. Baseline difficulty was NOT changed; target remains as specified.
2. **Small test set**: n=191 (~30 per class); per-class metrics have high variance. Results are directional, not proof.
3. **Challenge set n=39**: too small for statistical significance; author-written and AI-assisted, not used for tuning.
4. **Guardrail value rests on 3 errors**: flagged accuracy is 10/13 flagged tickets correct; 3 of 3 errors caught. Small-sample caveat applies.
5. **Team routing on challenge set is flat** (+0.1 points): account security drops to 0.600 F1 as Roman-Urdu and ambiguous tickets are misrouted to tech support.
6. **Urgency is derived from issue type**, not independently labeled; baseline uses rules-based urgency keywords, LLM/guardrails derive urgency from predicted issue type.

## PII Bug Found and Fixed

- **Bug**: In `guardrails.py` `classify_with_guardrails()`, PII was redacted for the record but the **original** subject/body was still passed to the LLM classifier and baseline fallback — violating the "PII redacted before any LLM call" requirement (requirements.md #3).
- **Fix** (commit 18b0ad6): subject and body are now redacted first, then redacted text is passed to all classifiers. Regression test `test_llm_receives_no_pii` added; confirmed FAILS on pre-fix commit, PASSES after fix.

## Questions for the Mentor

1. [ ]
2. [ ]
3. [ ]

## Mentor Feedback

(To be filled by mentor)
