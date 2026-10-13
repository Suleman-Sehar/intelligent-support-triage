# Responsible Use Statement

## System Overview
**Intelligent Support Triage** - Automated ticket classification system for SaaS helpdesk.
Classifies incoming support tickets by issue type (6 classes) and routes to team (4 classes).

## Intended Use
- **Primary**: Automatic routing of support tickets to correct team
- **Secondary**: Analytics on ticket volume by category
- **Human-in-the-loop**: Low-confidence predictions flagged for human review

## Out of Scope
- Automated responses or resolutions
- Customer-facing decisions without human oversight
- High-stakes decisions (account termination, billing disputes > $X)
- Multi-language support (English only)

## Fairness & Bias Considerations

### Training Data
- **Source**: Synthetic tickets generated from templates (1000 samples)
- **Limitation**: Synthetic data may not reflect real-world distribution, language diversity, or edge cases
- **Risk**: Model may underperform on:
  - Non-native English speakers
  - Regional dialects/colloquialisms
  - Complex multi-issue tickets
  - Tickets with heavy technical jargon

### Demographic Fairness
- No demographic data used in classification
- PII redacted before classification (emails, phones, names)
- However: Writing style correlates with demographics; potential for disparate impact

### Class Balance
| Issue Type | Train Count | Test Count |
|------------|-------------|------------|
| billing | ~133 | ~25 |
| bug | ~133 | ~25 |
| account access | ~133 | ~25 |
| feature request | ~133 | ~25 |
| how-to | ~133 | ~25 |
| outage | ~133 | ~25 |

Balanced by design in synthetic generator. Real data likely imbalanced (more how-to, fewer outages).

## Privacy & Data Protection

### PII Handling
- **Redaction before LLM**: Emails, phones, API keys, credit cards, SSN, IPs redacted
- **Redaction patterns**: Regex-based, applied to subject + body
- **Rate**: 26.7% of test tickets had PII redacted
- **LLM never sees raw PII**: Redacted text passed to API

### Data Retention
- **Cache**: LLM responses cached locally (SHA256 of input text)
- **Cache TTL**: No automatic expiration - manual cleanup needed
- **Predictions**: Saved to CSV in evidence/ (gitignored)
- **No persistent logging** of raw ticket content

### API Provider
- **Provider**: OpenRouter (gpt-4o-mini)
- **Data sent**: Redacted ticket text only
- **Provider policy**: Review OpenRouter/OpenAI data usage policies
- **No training**: API calls not used for model training (per provider terms)

## Transparency & Explainability

### Confidence Scores
- LLM provides confidence (0-1) with each prediction
- Threshold: 0.75 for human review
- Test set: 0% below threshold (LLM), 11% (fallback)

### Reasoning
- LLM provides brief reasoning for each classification
- Stored in predictions for audit trail
- Example: "Billing inquiry about invoice discrepancy and payment retry"

### Fallback Transparency
- When LLM fails, rules classifier used
- `fallback_used` flag in predictions
- Reasoning includes "Fallback to rules classifier"

## Safety & Reliability

### Failure Modes
| Failure | Mitigation |
|---------|------------|
| LLM API timeout/error | Fallback to rules classifier (3 retries with backoff) |
| Schema validation failure | Retry up to 3x, then fallback |
| Low confidence | Human review queue (threshold 0.75) |
| PII leakage | Pre-classification redaction + post-hoc audit |
| Concept drift | Periodic re-evaluation on fresh data |

### Monitoring Metrics (Production)
- Prediction latency (target P95 < 500ms)
- Human review rate (target < 15%)
- Fallback rate (target < 5%)
- Class distribution shift (KS test on confidence scores)
- Accuracy on human-reviewed samples (monthly audit)

### Incident Response
1. **High fallback rate**: Check API status, review error logs
2. **High human review**: Lower threshold or investigate data shift
3. **PII in logs**: Immediate cache clear, rotate API keys, audit
4. **Systematic misclassification**: Trigger retraining/evaluation cycle

## Governance

### Model Versioning
- Current: gpt-4o-mini via OpenRouter (2024)
- Pin model version in production
- A/B test before model upgrades

### Change Control
- All prompt/schema changes require evaluation on test set
- Regression test: F1 must not drop > 2%
- Document changes in decision_log.md

### Audit Trail
- Git history for code/config
- Timestamped evidence/ for each evaluation
- Prediction CSVs with ground truth for dispute resolution

## Limitations Disclosure

1. **Synthetic evaluation**: Metrics on generated data, not real tickets
2. **English only**: No validation on other languages
3. **Single model**: No ensemble or calibration
4. **Static threshold**: 0.75 not optimized per class
5. **No uncertainty quantification**: Confidence not calibrated
6. **Template bias**: Generator templates may create artificial patterns

## Recommendations for Production Deployment

1. **Shadow mode**: Run alongside human triage for 2+ weeks before cutover
2. **Gradual rollout**: Start with low-risk categories (how-to, feature request)
3. **Human feedback loop**: Collect corrections, retrain/finetune quarterly
4. **Real data evaluation**: Benchmark on 1000+ real tickets before launch
5. **Bias audit**: Test on stratified samples by customer segment
6. **Calibration**: Temperature scaling or Platt scaling on confidence scores
7. **Alerting**: Automated alerts for metric degradation

## Compliance Considerations

- **GDPR**: PII redaction, right to deletion (cache cleanup), DPIA recommended
- **SOC2**: Audit trails, access controls on prediction logs
- **Industry**: No regulated data (health, finance) in current scope

## Contact
For questions about this system: [team@company.com]
Last updated: 2026-10-13
Version: 1.0 (Phase 6)