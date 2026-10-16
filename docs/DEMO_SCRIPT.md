# Demo Script — 5-Minute Run Sheet

**Prerequisites:** `.venv` activated, `requirements.txt` installed.  
**API key:** optional — rules-only fallback if not set.  
**Total time:** 5 minutes

---

## 0. Setup (30 sec)

```bash
.venv\Scripts\activate
# Optional API key (set only if you have one):
# $env:OPENAI_API_KEY="sk-or-v1-..."
```

**Expected output:** venv activated, no errors.

---

## 1. Problem Statement (30 sec)

**Say:** "Support teams waste hours manually routing tickets. Misrouted tickets delay resolution and increase churn risk. We automate triage with a rules baseline, an LLM classifier, and PII guardrails."

**No commands.** Verbal only.

---

## 2. Live Classification (2 min)

**Scenario A — Billing ticket (no PII):**

```bash
python -c "
import sys; sys.path.insert(0,'src')
from guardrails import GuardrailPipeline
pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
r = pipe.classify_with_guardrails('Invoice question', 'I was charged twice this month')
print(f'Issue: {r.issue_type}, Team: {r.team}, Confidence: {r.confidence:.2f}')
print(f'Human review: {r.human_review}, PII redacted: {r.pii_redacted}')
"
```

**Expected output:**
```
Issue: billing, Team: billing, Confidence: 0.99
Human review: False, PII redacted: False
```

**Scenario B — PII ticket (redacted before any classifier):**

```bash
python -c "
import sys; sys.path.insert(0,'src')
from guardrails import GuardrailPipeline
pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
r = pipe.classify_with_guardrails(
    'Account issue',
    'My email is john.doe@example.com and phone is +1-555-123-4567. Please help.'
)
print(f'Issue: {r.issue_type}, Team: {r.team}')
print(f'PII redacted: {r.pii_redacted}')
print(f'Redacted: {r.redacted_text[:120]}')
"
```

**Expected output:**
```
Issue: account access, Team: account security
PII redacted: True
Redacted: [EMAIL] and phone is [PHONE]. Please help.
```

**Say:** "PII is redacted before the classifier ever sees it — verified by regression test."

---

## 3. Guardrails Demo (1 min)

**Vague ticket flagged for review:**

```bash
python -c "
import sys; sys.path.insert(0,'src')
from guardrails import GuardrailPipeline
pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
r = pipe.classify_with_guardrails('Help', 'help')
print(f'Human review: {r.human_review}, Confidence: {r.confidence:.2f}')
"
```

**Expected output:**
```
Human review: True, Confidence: 0.50
```

**Say:** "Short/vague tickets get flagged for human review instead of wrong auto-routing."

**Fallback demo (--no-llm):**

```bash
python src/guardrails.py --input data/tickets.csv --split test --output evidence/guardrail_predictions_test.csv --no-llm --threshold 0.75 | Select-Object -First 8
```

**Expected output:**
```
Processing 191 tickets from test split...
Guardrail Metrics (test):
  Issue Type Macro F1: 0.9683
  Team Macro F1:       0.9228
  Human Review Rate:   10.99%
```

---

## 4. Evaluation Dashboard (1 min)

**Open the latest report:**

```bash
# PowerShell: open the report
notepad evidence\evaluation_latest.md
```

**Say:** "Highlight: product team +20.7 points F1 improvement, human review 6.81% (≤15% target), PII redacted 26.70%."

**If you have an API key (optional, adds ~1 min):**

```bash
$env:OPENAI_API_KEY="<key>"
python src/llm_classifier.py --input data/tickets.csv --split test --output evidence/llm_predictions_test.csv --base-url "https://openrouter.ai/api/v1"
python src/guardrails.py --input data/tickets.csv --split test --output evidence/guardrail_predictions_test.csv --base-url "https://openrouter.ai/api/v1"
python src/evaluate.py --input data/tickets.csv --split test --baseline evidence/baseline_predictions_test.csv --llm evidence/llm_predictions_test.csv --guardrail evidence/guardrail_predictions_test.csv --guardrail-fallback evidence/guardrail_fallback_test.csv --output-dir evidence --name evaluation
```

---

## 5. Responsible AI (30 sec)

**Say:** "PII is never sent to the LLM — verified by test_llm_receives_no_pii. The system degrades to rules-only mode without an API key. Results on synthetic data are directional, not proof."

---

## Fallback if the API Fails During Demo

**If LLM calls fail or no key is set:**

1. Use `--no-llm` on guardrails.py (rules-only fallback).
2. Use cached results in `evidence/` (committed dated reports).
3. Say: "The LLM path requires an API key; here's the rules-only path that produces the same pipeline without one."

**Demo commands still work:** generate_tickets.py, baseline_classifier.py, guardrails.py --no-llm, evaluate.py (rules-only), pytest.

---

## End of Demo

**Final say:** "All code, tests, and evidence are committed to the repo. Full pipeline regenerates identically with seed 42."
