# Intelligent Support Triage

Automated ticket classification system for SaaS helpdesk. Classifies incoming support tickets by issue type (6 classes) and routes to team (4 classes) using LLM with guardrails.

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI-compatible API key (OpenRouter, OpenAI, etc.)

### Installation
```bash
git clone <repo-url>
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

### Run Tests
```bash
pytest tests/ -v
```

## Project Structure
```
intelligent-support-triage/
├── data/                    # Synthetic tickets (gitignored, reproducible)
├── src/
│   ├── generate_tickets.py  # Synthetic data generator
│   ├── baseline_classifier.py  # Rules-based baseline
│   ├── llm_classifier.py    # LLM with schema validation, retry, cache
│   ├── guardrails.py        # PII redaction, threshold, fallback
│   └── evaluate.py          # Comparison table generator
├── evidence/                # Evaluation outputs (gitignored)
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── requirements.md          # Requirements & acceptance criteria
├── decision_log.md          # Key decisions
├── work_log.md              # Phase-by-phase progress
├── error_analysis.md        # Misclassification analysis
├── responsible_use.md       # Privacy, fairness, governance
├── requirements.txt         # Python dependencies
└── .gitignore
```

## Key Results (Test Split, 191 tickets)

| Metric | Baseline (Rules) | LLM (gpt-4o-mini) | Improvement |
|--------|------------------|-------------------|-------------|
| Issue Type Macro F1 | 0.968 | 0.984 | +1.5% |
| Team Macro F1 | 0.923 | 0.983 | +6.0% |
| Avg Confidence | 0.866 | 0.941 | +8.6% |
| Human Review Rate | N/A | 0.0% | ✓ |
| PII Redacted Rate | N/A | 26.7% | ✓ |

**Per-class Team F1 gains:**
- Product: 0.793 → 1.000 (+20.7%)
- Billing: 0.967 → 1.000 (+3.3%)
- Tech Support: 0.931 → 0.985 (+5.4%)
- Account Security: 1.000 → 0.947 (-5.3%)

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxx  # OpenRouter or OpenAI key
OPENAI_BASE_URL=https://openrouter.ai/api/v1  # Optional: for OpenRouter
```

### Guardrails Settings
- Confidence threshold: 0.75 (configurable via `--threshold`)
- PII patterns: email, phone, API keys, credit cards, SSN, IP
- Max retries: 3 with exponential backoff
- Cache: local disk (SHA256 of input)

## Demo Outline (5 min)

### 1. Problem Statement (30 sec)
"Support teams waste time manually routing tickets. We automate this with 98% accuracy."

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
- Show 0% human review rate

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
- Outputs: predictions CSV + per-class F1

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
| Baseline Issue F1 | ≥ 0.70 | 0.968 | ✅ |
| Baseline Team F1 | ≥ 0.70 | 0.923 | ✅ |
| LLM Issue F1 improvement | ≥ 0.10 | +0.015 | ❌* |
| LLM Team F1 improvement | ≥ 0.10 | +0.060 | ❌* |
| Human review rate | ≤ 15% | 0% | ✅ |
| PII redaction | Working | 26.7% | ✅ |
| Reproducible in ≤5 cmds | Yes | 5 commands | ✅ |

*Baseline already very high on synthetic data; improvement target unrealistic for this dataset.

## Known Limitations

1. **Synthetic evaluation only** - No real ticket validation
2. **English only** - No multilingual support
3. **Account access regression** - "How to" pattern confuses LLM (-5.3% F1)
4. **Confidence not calibrated** - Threshold 0.75 arbitrary
5. **Single model** - No ensemble or A/B testing framework
6. **Cache grows unbounded** - No TTL/cleanup

## Future Work

- [ ] Evaluate on 1000+ real tickets
- [ ] Finetune smaller model for lower latency/cost
- [ ] Add confidence calibration (temperature scaling)
- [ ] Implement cache TTL and size limits
- [ ] Add drift detection (confidence distribution monitoring)
- [ ] Build simple UI for human review queue
- [ ] Add multi-language support

## License

MIT License - see LICENSE file

## Contact

Built for Arrowstack Internship - Intelligent Support Triage Project