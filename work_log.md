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
| 2026-10-13 | Phase 8 | GitHub repo created & pushed (https://github.com/Suleman-Sehar/intelligent-support-triage) | ✓ |
| 2026-10-13 | Phase 8 | SLIDES_OUTLINE.md (12 slides), demo.py (live demo script) | ✓ |
| 2026-10-13 | Phase 8 | RESUME_BULLETS.md, LINKEDIN_POST.md | ✓ |
| 2026-10-13 | Gap Fix 1 | Overconfidence guardrails: vague ticket detection (short, few keywords, vague words without intent), baseline vs LLM disagreement flag; 10 edge cases all flagged for review (100%); updated guardrails.py, added data/edge_cases.csv | ✓ |
| 2026-10-13 | Gap Fix 2 | Evidence committed: removed evidence/* from .gitignore, committed dated evaluation snapshot; verified fresh clone regenerates data/tickets.csv identically (seed 42, MD5 fbf4c66dbe9a181013876e98a46ebc91) | ✓ |
| 2026-10-13 | Gap Fix 3 | Edge case tests: test_edge_cases.py with 12 tests (empty/None/long/Unicode, LLM retry, timeout fallback, vague ticket) - 16 total tests passing | ✓ |
| 2026-10-14 | Gap Fix 4 | Honest reporting: added dated entry on LLM improvement target not met (synthetic data limitation); added per-slice results (easy/hard/edge) to evaluate.py; noted test set size/noise in error_analysis.md and README | ✓ |
| 2026-10-14 | Gap Fix 5 | Docs only: added cache TTL/LRU, multi-label, calibration docs to README and responsible_use.md | ✓ |
| 2026-10-14 | Phase 9 Step 1 | Vague-ticket check: 5/5 vague tickets flagged for review; 10/10 edge cases flagged (100% review rate) | ✓ |
| 2026-10-14 | Phase 9 Step 2 | Evidence: confirmed dated reports tracked, no symlinks, fixed README evidence/ comment | ✓ |
| 2026-10-14 | Phase 9 Step 3 | Added "How to read this" note to evaluation; per-slice results (easy/hard/edge by confidence) present | ✓ |
| 2026-10-16 | Debug | Ran full pipeline; fixed PII sent to LLM in guardrails.py (redact subject/body before baseline/LLM calls) | ✓ |
| 2026-10-16 | Task 1 | Cache key check: cache built on text passed to classify() (redacted after fix 18b0ad6); cleared 722 cache entries, reran LLM on test split — no prediction changes | ✓ |
| 2026-10-16 | Task 2 | Provider consistency: code reads OPENAI_API_KEY only; created .env.example; README aligned | ✓ |
| 2026-10-16 | Task 3 | LLM path rerun with real API key: dev 809/809 (Issue F1 0.9911, Team F1 0.9946); test 191/191 (Issue F1 0.9838, Team F1 0.9830) | ✓ |
| 2026-10-16 | Task 4 | Urgency metrics added to evaluate.py: outage=critical, bug/account access=high, billing=medium, feature request/how-to=low; Urgency Macro F1 0.9883 | ✓ |
| 2026-10-16 | Task 5 | Guardrail value: auto-routed accuracy 100% (178 tickets), flagged accuracy 76.92% (13 tickets), 100% of errors caught | ✓ |
| 2026-10-16 | Task 6 | Challenge set: data/challenge_set.csv with 39 hand-labeled tickets; LLM Issue F1 0.8382 vs baseline 0.7699 on challenge set | ✓ |
| 2026-10-16 | Task 7 | Docs: README updated (6.8% review rate, OpenRouter provider), stale ~30 per class removed, error_analysis.md updated | ✓ |
| 2026-10-16 | Task 8 | pytest: 17 passed; new dated evidence saved as real files (no symlinks) | ✓ |
| 2026-10-16 | Step 1 | Challenge set rerun: baseline Issue F1 0.7699, LLM Issue F1 0.8382 (+0.0683 points); dated evidence saved | ✓ |
| 2026-10-16 | Step 2 | Docs: percentages converted to points in README/error_analysis.md; challenge set described as "author-written, AI-assisted" | ✓ |