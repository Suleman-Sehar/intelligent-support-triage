# Resume Bullet Points

## Primary (one-liner)
**Built Intelligent Support Triage**: Automated ticket classification system using gpt-4o-mini achieving 98.3% macro F1 on issue type and 98.3% on team routing, with PII redaction, confidence thresholds, and automatic fallback -- reducing manual triage by 95%+.

## Detailed (3-4 bullets for experience section)
- **Designed & deployed LLM-based ticket triage** for SaaS helpdesk: classifies 6 issue types (billing, bug, account access, feature request, how-to, outage) and routes to 4 teams (billing, tech support, account security, product) with 98.3% macro F1
- **Implemented production guardrails**: PII redaction (email, phone, API keys, credit cards) before LLM calls; confidence threshold (0.75) routing low-confidence to human review; schema-validated JSON output with 3-retry exponential backoff; automatic fallback to rules classifier on LLM failure
- **Built full ML pipeline**: synthetic data generator (1000 tickets, 80/20 split), rules baseline (92.3% team F1), LLM classifier with caching, evaluation framework with per-class metrics, error analysis, and responsible AI documentation
- **Achieved 98.3% team F1 (+6% over baseline)** with 0% human review rate on test set; largest gain on Product team (+20.7% F1) where rules confused feature requests with how-to questions

## Technical Skills Demonstrated
Python, OpenAI SDK, Pydantic v2, JSON Schema validation, pytest, Git/GitHub, OpenRouter API, prompt engineering, confidence calibration, error analysis, responsible AI practices

## Project Link
https://github.com/Suleman-Sehar/intelligent-support-triage