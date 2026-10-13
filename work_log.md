# Work Log

| Date | Phase | Activity | Status |
|------|-------|----------|--------|
| 2026-10-13 | Phase 0 | Environment check completed | ✓ |
| 2026-10-13 | Phase 0 | Git repo initialized | ✓ |
| 2026-10-13 | Phase 0 | Folder structure created (data, src, tests, evidence, docs) | ✓ |
| 2026-10-13 | Phase 0 | requirements.md written | ✓ |
| 2026-10-13 | Phase 0 | decision_log.md created | ✓ |
| 2026-10-13 | Phase 0 | work_log.md created | ✓ |
| 2026-10-13 | Phase 1 | Synthetic ticket generator created (src/generate_tickets.py) | ✓ |
| 2026-10-13 | Phase 1 | 1000 tickets generated (data/tickets.csv, 80/20 dev/test split) | ✓ |
| 2026-10-13 | Phase 2 | Rules-based baseline classifier created (src/baseline_classifier.py) | ✓ |
| 2026-10-13 | Phase 2 | Baseline metrics (dev): Issue F1=0.968, Team F1=0.937 | ✓ |
| 2026-10-13 | Phase 2 | Baseline metrics (test): Issue F1=0.968, Team F1=0.923 | ✓ |
| 2026-10-13 | Phase 3 | LLM classifier with schema validation, retry, cache (src/llm_classifier.py) | ✓ |
| 2026-10-13 | Phase 3 | LLM metrics (test): Issue F1=0.984, Team F1=0.983 (Δ +1.6%, +6.0% vs baseline) | ✓ |
| 2026-10-13 | Phase 4 | Guardrails pipeline (src/guardrails.py): PII redaction, confidence threshold, human review, fallback | ✓ |
| 2026-10-13 | Phase 4 | Guardrail metrics (test, LLM): Issue F1=0.984, Team F1=0.983, 0% human review, 26.7% PII redacted | ✓ |
| 2026-10-13 | Phase 4 | Guardrail metrics (test, fallback): Issue F1=0.968, Team F1=0.923, 11% human review | ✓ |
| 2026-10-13 | Phase 5 | Evaluation script (src/evaluate.py) with comparison table | ✓ |
| 2026-10-13 | Phase 5 | Evidence saved: evaluation_latest.md/json, timestamped files in evidence/ | ✓ |
| 2026-10-13 | Phase 6 | Error analysis (error_analysis.md): 2 issue-type errors, 1 team error, product +20.7% F1 | ✓ |
| 2026-10-13 | Phase 6 | Responsible use statement (responsible_use.md): privacy, fairness, limitations, governance | ✓ |
| 2026-10-13 | Phase 7 | README.md with 5-command reproduction, demo outline, API reference | ✓ |
| 2026-10-13 | Phase 7 | requirements.txt, tests/test_core.py (4 tests passing) | ✓ |
| 2026-10-13 | Phase 7 | Final QA: pipeline verified end-to-end | ✓ |