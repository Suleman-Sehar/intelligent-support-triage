# LinkedIn Post

Just wrapped up my Arrowstack internship project: **Intelligent Support Triage** -- an automated ticket classification system for SaaS helpdesks.

## The Problem
Support teams spend 20%+ of their time manually routing tickets to the right team. With 6 issue types x 4 teams = 24 routing combinations, errors mean delayed responses and frustrated customers.

## The Solution
Built an LLM-powered triage system (gpt-4o-mini via OpenRouter) with production-grade guardrails:

- **Classification**: 98.3% macro F1 on issue type, 98.3% on team routing (test set, 191 tickets)
- **Guardrails**: 
  - PII redaction (email, phone, API keys, credit cards) BEFORE LLM call -- 26.7% of tickets had PII
  - Confidence threshold (0.75) -> human review queue (0% review rate with LLM)
  - Schema-validated JSON output with 3-retry exponential backoff
  - Automatic fallback to rules classifier on LLM failure

- **Biggest win**: Product team routing jumped from 79.3% -> 100% F1 (+20.7%) -- LLM correctly distinguishes "I want this feature" vs "How do I use this?"

## Tech Stack
Python 3.11 * OpenAI SDK * Pydantic v2 * JSON Schema * pytest * GitHub Actions ready

## Reproducible in 5 commands:
```bash
git clone https://github.com/Suleman-Sehar/intelligent-support-triage
cd intelligent-support-triage && python -m venv .venv && pip install -r requirements.txt
python src/generate_tickets.py -n 1000 -s 42
python src/baseline_classifier.py --split test
python src/llm_classifier.py --split test --base-url "https://openrouter.ai/api/v1"
python src/guardrails.py --split test --base-url "https://openrouter.ai/api/v1"
python src/evaluate.py
```

## Responsible AI
Documented limitations (synthetic data only, English only, confidence not calibrated), privacy (PII never sent to LLM), fairness (no demographic data), and governance (model versioning, change control, audit trail).

**GitHub**: https://github.com/Suleman-Sehar/intelligent-support-triage

#MachineLearning #LLM #NLP #SupportAutomation #ResponsibleAI #ArrowstackInternship #OpenSource