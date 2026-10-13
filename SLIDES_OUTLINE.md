# Intelligent Support Triage - Slide Deck Outline

## Slide 1: Title
**Intelligent Support Triage**
Automated ticket classification for SaaS helpdesk
*Arrowstack Internship Project | Suleman Sehar*

---

## Slide 2: Problem
**Support teams waste 20%+ time manually routing tickets**
- 6 issue types x 4 teams = 24 routing combinations
- Inconsistent classification -> delayed responses
- PII exposure risk when forwarding tickets
- No confidence scoring for human review

---

## Slide 3: Solution
**LLM-powered triage with production guardrails**
- Classifies issue type (6 classes) + team (4 classes)
- 98.3% macro F1 on test set (vs 92.3% baseline)
- PII redaction before LLM call (26.7% tickets)
- Confidence threshold -> human review queue
- Automatic fallback to rules classifier

---

## Slide 4: Architecture
```
Ticket -> PII Redaction -> LLM (gpt-4o-mini) -> Schema Validation
                  |              |
              Confidence Check -> Human Review Queue (if < 0.75)
                  |
              Fallback: Rules Classifier (if LLM fails)
                  |
              Output: issue_type, team, confidence, reasoning
```

---

## Slide 5: Results - Test Set (191 tickets)

| Metric | Baseline (Rules) | LLM + Guardrails | Delta |
|--------|------------------|------------------|-------|
| Issue Type F1 | 0.968 | 0.984 | +1.5% |
| Team F1 | 0.923 | 0.983 | +6.0% |
| Human Review | N/A | 0% | PASS |
| PII Redacted | N/A | 26.7% | PASS |

**Per-team gains:**
- Product: 0.793 -> 1.000 (**+20.7%**)
- Billing: 0.967 -> 1.000
- Tech Support: 0.931 -> 0.985

---

## Slide 6: Guardrails in Action

**PII Redaction** (before LLM)
```
"Contact me at john@company.com, phone +1-555-123-4567"
-> "Contact me at [EMAIL], phone [PHONE]"
```

**Confidence Threshold**
- Threshold: 0.75
- LLM mode: 0% human review (all high confidence)
- Fallback mode: 11% human review

**Fallback**
- 3 retries with exponential backoff
- Schema validation on every response
- Automatic switch to rules classifier

---

## Slide 7: Error Analysis
**Only 3 errors on 191 tickets**

| Error Type | Count | Root Cause |
|------------|-------|------------|
| Account Access -> How-To | 1 | "How do I reset 2FA?" triggers how-to keyword |
| Account Security -> Tech Support | 1 | Follows issue type error |
| (How-To FP) | 1 | Other class predicted as how-to |

**Biggest win:** Product team +20.7% F1 (LLM distinguishes "I want feature" vs "How do I use")

---

## Slide 8: Responsible AI
- **Privacy**: PII redacted before API call, local caching only
- **Fairness**: Synthetic data limitations documented, no demographic data used
- **Transparency**: Confidence scores, reasoning, fallback flags in every prediction
- **Safety**: Human-in-the-loop, monitored fallback rate, incident response plan
- **Governance**: Model versioning, change control, audit trail

---

## Slide 9: Reproducibility
**5 commands from clean clone:**
```bash
git clone https://github.com/Suleman-Sehar/intelligent-support-triage
cd intelligent-support-triage
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
python src/generate_tickets.py -n 1000 -s 42
python src/baseline_classifier.py --split test
$env:OPENAI_API_KEY="..."; python src/llm_classifier.py --split test --base-url "https://openrouter.ai/api/v1"
python src/guardrails.py --split test --base-url "https://openrouter.ai/api/v1"
python src/evaluate.py
```

---

## Slide 10: Tech Stack
- **Python 3.11**, OpenAI SDK, Pydantic v2
- **LLM**: gpt-4o-mini via OpenRouter
- **Validation**: JSON Schema + Pydantic
- **Testing**: pytest (4 core tests passing)
- **CI/CD ready**: GitHub Actions compatible

---

## Slide 11: Future Work
- [ ] Evaluate on 1000+ real tickets
- [ ] Finetune smaller model (lower latency/cost)
- [ ] Add confidence calibration (temperature scaling)
- [ ] Implement cache TTL and size limits
- [ ] Add drift detection (confidence distribution monitoring)
- [ ] Build simple UI for human review queue
- [ ] Add multi-language support

---

## Slide 12: Thank You
**GitHub**: https://github.com/Suleman-Sehar/intelligent-support-triage
**Contact**: Suleman Sehar | [LinkedIn]

*Built during Arrowstack Internship*