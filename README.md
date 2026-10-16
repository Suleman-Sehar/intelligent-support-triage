# Intelligent Support Triage

Automated ticket classification system for SaaS helpdesk. Classifies incoming support tickets by issue type (6 classes), urgency (4 levels), and routes to team (4 classes) using LLM with guardrails.

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI-compatible API key (OpenRouter, OpenAI, etc.)

### Installation
```bash
git clone https://github.com/Suleman-Sehar/intelligent-support-triage.git
cd intelligent-support-triage
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key
```

### Reproduce Full Pipeline (5 commands)
```bash
# 1. Generate synthetic data
python src/generate_tickets.py -n 1000 -s 42 -o data/tickets.csv

# 2. Run baseline classifier
python src/baseline_classifier.py --input data/tickets.csv --split test --output evidence/baseline_predictions_test.csv

# 3. Run LLM classifier (requires API key)
$env:OPENAI_API_KEY="your-key"; python src/llm_classifier.py --input data/tickets.csv --split test --output evidence/llm_predictions_test.csv --base-url "https://openrouter.ai/api/v1"

# 4. Run guardrails pipeline
$env:OPENAI_API_KEY="your-key"; python src/guardrails.py --input data/tickets.csv --split test --output evidence/guardrail_predictions_test.csv --base-url "https://openrouter.ai/api/v1"

# 5. Generate evaluation report
python src/evaluate.py --input data/tickets.csv --split test --baseline evidence/baseline_predictions_test.csv --llm evidence/llm_predictions_test.csv --guardrail evidence/guardrail_predictions_test.csv --guardrail-fallback evidence/guardrail_fallback_test.csv --output-dir evidence --name evaluation
```

### Running Without an API Key
If no API key is available, skip steps 3-4 and use rules-only mode:
```bash
# Step 4 (rules-only fallback, no LLM)
python src/guardrails.py --input data/tickets.csv --split test --output evidence/guardrail_predictions_test.csv --no-llm

# Step 5 (evaluate rules-only results as both LLM and fallback)
python src/evaluate.py --input data/tickets.csv --split test --baseline evidence/baseline_predictions_test.csv --llm evidence/guardrail_predictions_test.csv --guardrail evidence/guardrail_predictions_test.csv --guardrail-fallback evidence/guardrail_predictions_test.csv --output-dir evidence --name evaluation
```
**Without API key**: `llm_classifier.py` exits with error. `guardrails.py` with `--no-llm` falls back to rules. No cached results are used (cache is empty on fresh clone).

### Run Tests
```bash
pytest tests/ -v
```

## Project Structure
```
intelligent-support-triage/
├── data/
│   ├── tickets.csv            # Synthetic tickets (gitignored, reproducible, seed 42)
│   ├── edge_cases.csv         # 10 edge-case tickets
│   └── challenge_set.csv      # 39 hand-labeled challenge tickets (author-written, AI-assisted)
├── src/
│   ├── generate_tickets.py    # Synthetic data generator
│   ├── baseline_classifier.py # Rules-based baseline (issue type, team, urgency)
│   ├── llm_classifier.py      # LLM with schema validation, retry, cache
│   ├── guardrails.py          # PII redaction, threshold, fallback
│   └── evaluate.py            # Comparison table generator (urgency, guardrail value)
├── evidence/                  # Evaluation outputs (committed: dated reports + latest)
├── tests/                     # Unit tests
├── docs/                      # Documentation (MENTOR_REVIEW.md, SLIDES_OUTLINE.md, DEMO_SCRIPT.md)
├── requirements.md            # Requirements & acceptance criteria
├── decision_log.md            # Key decisions
├── work_log.md                # Phase-by-phase progress
├── error_analysis.md          # Misclassification analysis
├── responsible_use.md         # Privacy, fairness, governance
├── requirements.txt           # Python dependencies
├── .gitignore
└── README.md
```

## Key Results (Test Split, 191 tickets)

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Improvement |
|--------|------------------|-------------------|-------------|
| Issue Type Macro F1 | 0.968 | 0.984 | +1.6 points |
| Team Macro F1 | 0.923 | 0.983 | +6.0 points |
| Urgency Macro F1 | 0.856 | 0.988 | +13.2 points |
| Urgency High/Critical Recall | 80.0% | 96.8% | +16.8 pts |
| Avg Confidence | 0.866 | 0.941 | +0.08 |
| Human Review Rate | N/A | 6.8% | ✓ |
| PII Redacted Rate | N/A | 26.7% | ✓ |

**Per-class Team F1 gains (points = F1 x 100):**
- Product: 0.793 → 1.000 (+20.7 points)
- Billing: 0.967 → 1.000 (+3.3 points)
- Tech Support: 0.931 → 0.985 (+5.4 points)
- Account Security: 1.000 → 0.947 (-5.3 points)

**Challenge set** (author-written, AI-assisted, 39 tickets, not used for tuning):
- Baseline Issue F1: 0.770 | LLM Issue F1: 0.838 (+6.8 points)
- Baseline Team F1: 0.824 | LLM Team F1: 0.825 (+0.1 points — no meaningful gain). Root cause: account security team drops to 0.600 F1 on challenge set (Roman-Urdu and ambiguous tickets misrouted to tech support).

## Configuration
### Environment Variables (.env)

```bash
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxx  # OpenAI-compatible key (OpenRouter, OpenAI, etc.)
# Base URL is set via --base-url CLI flag (default: https://openrouter.ai/api/v1)
```

### Guardrails Settings
- Confidence threshold: 0.75 (configurable via `--threshold`)
- PII patterns: email, phone, API keys, credit cards, SSN, IP
- Max retries: 3 with exponential backoff
- Cache: local disk (SHA256 of input)

**PII bug fix** (commit 18b0ad6): PII was previously redacted for the record but the original subject/body was still passed to the LLM and baseline classifiers — violating the "PII redacted before any LLM call" requirement. Fixed by redacting subject and body first, then passing redacted text to all classifiers. Regression test `test_llm_receives_no_pii` (tests/test_edge_cases.py) confirms the LLM receives no email/phone/API-key/card/SSN/IP patterns; it fails on the pre-fix commit and passes after 18b0ad6.

## Demo Outline (5 min)

### 1. Problem Statement (30 sec)
"Support teams waste time manually routing tickets. We automate triage with LLM+guardrails; LLM reaches 0.984 issue-type macro-F1 on synthetic test data (both models near-ceiling; real-world gap larger on noisy data)."

### 2. Live Classification (2 min)
```bash
# Show single ticket classification
python -c "
from src.guardrails import GuardrailPipeline
from src.llm_classifier import LLMClassifier, PredictionCache
import os
os.environ['OPENAI_API_KEY'] = 'your-key'
cache = PredictionCache('cache')
llm = LLMClassifier(base_url='https://openrouter.ai/api/v1', cache=cache)
pipe = GuardrailPipeline(llm_classifier=llm)
result = pipe.classify_with_guardrails(
    'Invoice discrepancy', 
    'I was charged \$49.99 but my plan shows \$29.99. Invoice INV-2024-00123.'
)
print(f'Issue: {result.issue_type}, Team: {result.team}, Confidence: {result.confidence:.2f}')
print(f'PII Redacted: {result.pii_redacted}, Human Review: {result.human_review}')
"
```

### 3. Guardrails Demo (1 min)
- Show PII redaction on ticket with email/phone
- Show human review flag on low-confidence example
- Show fallback when LLM disabled

### 4. Evaluation Dashboard (1 min)
- Open `evidence/evaluation_latest.md` - comparison table
- Highlight product team +20.7% F1 improvement
- Show 6.8% human review rate

### 5. Responsible AI (30 sec)
- PII never sent to LLM
- Synthetic data limitations acknowledged
- Human-in-the-loop for edge cases

## API Reference

### generate_tickets.py
```bash
python src/generate_tickets.py -n 1000 -s 42 -o data/tickets.csv
```
- `-n`: number of tickets (default 1000)
- `-s`: random seed (default 42)
- `-o`: output CSV path

### baseline_classifier.py
```bash
python src/baseline_classifier.py --input data/tickets.csv --split test --output evidence/baseline_predictions_test.csv
```
- `--split`: dev or test
- Outputs: predictions CSV + per-class F1 (issue type, team, urgency)

### llm_classifier.py
```bash
python src/llm_classifier.py --input data/tickets.csv --split test --output evidence/llm_predictions_test.csv --model gpt-4o-mini --base-url https://openrouter.ai/api/v1 --limit 50
```
- `--model`: OpenAI model name
- `--base-url`: API endpoint (OpenRouter, etc.)
- `--limit`: process only N tickets (for testing)
- `--cache-dir`: cache directory (default "cache")

### guardrails.py
```bash
python src/guardrails.py --input data/tickets.csv --split test --output evidence/guardrail_predictions_test.csv --threshold 0.75 --model gpt-4o-mini --base-url https://openrouter.ai/api/v1
```
- `--threshold`: confidence threshold for human review (default 0.75)
- `--no-llm`: run rules-only fallback mode

### evaluate.py
```bash
python src/evaluate.py --input data/tickets.csv --split test --baseline evidence/baseline_predictions_test.csv --llm evidence/llm_predictions_test.csv --guardrail evidence/guardrail_predictions_test.csv --guardrail-fallback evidence/guardrail_fallback_test.csv --output-dir evidence --name evaluation
```
Generates markdown + JSON evidence in `evidence/`

**Example JSON output** (evidence/evaluation_latest.json):
```json
{
  "baseline": {
    "issue_type": { "macro_f1": 0.9683 },
    "team": { "macro_f1": 0.9228 },
    "urgency": { "macro_f1": 0.8562 },
    "urgency_high_critical_recall": 0.8,
    "avg_confidence": 0.8662,
    "human_review_rate": 0.1099,
    "pii_redacted_rate": 0.267,
    "num_samples": 191
  },
  "llm": {
    "issue_type": { "macro_f1": 0.9838 },
    "team": { "macro_f1": 0.983 },
    "urgency": { "macro_f1": 0.9883 },
    "urgency_high_critical_recall": 0.9684,
    "avg_confidence": 0.9411,
    "human_review_rate": 0.0,
    "pii_redacted_rate": 0.0,
    "num_samples": 191
  }
}
```

## Sample Output (single triage result, rules-only mode)

```json
{
  "issue_type": "billing",
  "urgency": "medium",
  "routing_team": "billing",
  "confidence": 0.95,
  "needs_human_review": false,
  "rationale": "Rules classifier (LLM disabled) | Keyword match on billing terms (charged, refund)"
}
```

Generated from ticket: subject="Double charged this month", body="I was charged twice this month for my subscription plan. Please refund the duplicate charge."

## Requirements
```
openai>=1.0.0
pydantic>=2.0.0
pandas>=2.0.0
scikit-learn>=1.3.0
pytest>=7.0.0
```

## Acceptance Criteria Status

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Baseline Issue F1 | >= 0.70 | 0.968 | PASS |
| Baseline Team F1 | >= 0.70 | 0.923 | PASS |
| LLM Issue F1 improvement | >= 0.10 | +1.5 points | FAIL* |
| LLM Team F1 improvement | >= 0.10 | +6.0 points | FAIL* |
| Human review rate | <= 15% | 6.8% | PASS |
| PII redaction | Working | 26.7% | PASS |
| Reproducible in <=5 cmds | Yes | 5 commands | PASS |

*Baseline already near-ceiling on synthetic data; improvement target unrealistic for this dataset (see decision_log.md)

## Known Limitations

1. **Synthetic evaluation only** - No real ticket validation
2. **Account access (issue type) regression** - "How to" pattern confuses LLM (-5.3 points F1 on test split)
3. **Account Security (team) drop on challenge set** - Drops to 0.600 F1; Roman-Urdu and ambiguous tickets misrouted to tech support. No meaningful team F1 gain on challenge set (+0.1 points).
4. **Confidence not calibrated** - Threshold 0.75 arbitrary (no temperature scaling, Platt, or isotonic calibration)
5. **Single model** - No ensemble or A/B testing framework
6. **Cache grows unbounded** - No TTL/cleanup (see Future Work)
7. **Single-label only** - Cannot handle tickets with multiple issues (e.g., billing + bug)

## Future Work

### Cache Management
- [ ] Add `ttl_hours` and `max_entries` params to `PredictionCache`
- [ ] Implement LRU eviction when cache exceeds `max_entries`
- [ ] Periodic cleanup of expired cache entries
- [ ] Add cache hit rate metrics to evaluation output

### Multi-Label Tickets
- [ ] Detect multiple issues in single ticket (top-k predictions with threshold)
- [ ] Add "multiple issues" flag and routing to senior support
- [ ] Update GuardrailResult to support list of (issue_type, confidence) pairs

### Confidence Calibration
- [ ] Plot confidence vs accuracy on dev set (reliability diagram)
- [ ] Add temperature scaling calibration step
- [ ] Use calibrated confidence for threshold optimization
- [ ] Report Expected Calibration Error (ECE) in evaluate.py

### Other Improvements
- [ ] Evaluate on 1000+ real tickets
- [ ] Finetune smaller model for lower latency/cost
- [ ] Add drift detection (confidence distribution monitoring)
- [ ] Build simple UI for human review queue
- [ ] Add multi-language support
- [ ] Add unit tests for calibration, cache TTL, multi-label logic

## License

MIT License - see LICENSE file

## Contact

Built by Suleman-Sehar for Arrowstack Internship - Intelligent Support Triage Project