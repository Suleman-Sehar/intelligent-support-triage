# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-13 | Company domain: SaaS helpdesk | Default per plan |
| 2026-10-13 | Labels: default issue types (6) and teams (4) | Default per plan, no mentor override |
| 2026-10-13 | Deliverable: slides (PPT) + short demo | Default per plan |
| 2026-10-13 | LLM provider: OpenAI (GPT-4o-mini) | Package installed, API key available |
| 2026-10-13 | Python 3.11 | Available and meets minimum |
| 2026-10-13 | Added rule-based guardrails for overconfidence | Vague/ambiguous tickets (short, few keywords, vague indicators without intent) now flagged for human review; baseline vs LLM disagreement triggers review; 10 edge cases all flagged |