# Requirements: Intelligent Support Triage

## Stakeholder
- **Primary**: Support operations team at a SaaS helpdesk company
- **Secondary**: Engineering team (integration), Product team (insights)

## Scope
Build an automated ticket triage system that classifies incoming support tickets by:
- **Issue type**: billing, bug, account access, feature request, how-to, outage
- **Team**: billing, tech support, account security, product

Route tickets to the correct team with confidence scores. Flag low-confidence predictions for human review.

## Out of Scope
- Auto-resolution or response generation
- Real-time streaming classification
- Multi-language support (English only for v1)

## Metrics
| Metric | Target |
|--------|--------|
| Macro F1 (issue type) | ≥ 0.85 |
| Macro F1 (team) | ≥ 0.88 |
| Human review rate | ≤ 15% |
| P95 latency | ≤ 500ms |

## Acceptance Criteria
1. Given a synthetic ticket dataset (dev/test split), the baseline rules classifier achieves ≥ 0.70 macro F1 on both tasks
2. The LLM classifier improves macro F1 by ≥ 10 points over baseline on test set
3. PII redaction removes emails, phone numbers, API keys, credit cards from ticket text before classification
4. Confidence threshold: tickets below 0.75 confidence routed to human review queue
5. Fallback: if LLM fails (timeout, error, schema violation), fall back to rules classifier
6. Evaluation script produces comparison table (baseline vs AI) and error analysis
7. Reproducible in ≤ 5 commands from clean clone (documented in README)

## Labels
**Issue Types** (6): billing, bug, account access, feature request, how-to, outage
**Teams** (4): billing, tech support, account security, product

## Deliverable
- Slides (PPT) + short live demo
- Public GitHub repo with reproducible pipeline

## Constraints
- Python 3.11+, OpenAI API (GPT-4o-mini or equivalent)
- No external data sources beyond synthetic generator
- Tune only on dev split; test split held out until final evaluation
- No API keys committed; use `.env` (gitignored)