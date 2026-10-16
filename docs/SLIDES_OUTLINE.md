# Support Triage — 8-Slide Deck Outline

Numbers match `evidence/evaluation_latest.md` (test split, 191 tickets) and `data/challenge_set.csv` (39 tickets).

---

## Slide 1 — Problem and Stakeholder

**Stakeholder:** SaaS helpdesk support operations (ticket routing team)

**Problem:** Support teams waste hours manually routing 1,000+ tickets/week. Misrouted tickets delay resolution and increase churn risk.

**Speaker notes:**
- Manual triage doesn't scale; every misrouted ticket costs hours in re-assignment and SLA breaches.
- Stakeholder owns routing accuracy and wants a system that flags ambiguous tickets for human review.

---

## Slide 2 — Approach

**Pipeline:** Generate synthetic data → Rules baseline → LLM classifier → Guardrails → Evaluate

**Baseline:** Keyword rules for issue type (6 classes) and team (4 classes)

**LLM:** gpt-4o-mini via OpenRouter (OPENAI_API_KEY), schema validation, retry, disk cache

**Guardrails:** PII redaction (before any classifier), confidence threshold 0.75, vague-ticket detection, human review flag, rules-only fallback

**Speaker notes:**
- Rules baseline is fast and interpretable; LLM handles nuance and paraphrase.
- Guardrails enforce privacy (PII redacted first) and safety (vague tickets → human review).
- Rules-only fallback keeps the system running without an API key.

---

## Slide 3 — Baseline vs AI Results

**Test split (191 tickets, synthetic, seed 42):**

| Metric | Baseline | LLM | Change |
|--------|----------|-----|--------|
| Issue Type Macro F1 | 0.9683 | 0.9838 | +1.6 points |
| Team Macro F1 | 0.9228 | 0.9830 | +6.0 points |
| Urgency Macro F1 | 0.8562 | 0.9883 | +13.2 points |
| High/Critical Urgency Recall | 80.00% | 96.84% | +16.8 pts |

**Challenge set (39 tickets, author-written, AI-assisted, not tuned):**

| Metric | Baseline | LLM | Change |
|--------|----------|-----|--------|
| Issue Type Macro F1 | 0.7699 | 0.8382 | +6.8 points |
| Team Macro F1 | 0.8241 | 0.8249 | +0.1 points (no gain) |

**Speaker notes:**
- LLM wins on both datasets; the gap widens on noisy challenge data (+6.8 pts vs +1.6 pts).
- Challenge team routing is flat: account security drops to 0.600 F1 on Roman-Urdu tickets.
- Improvement target (10 points) NOT met on synthetic data — baseline is already near-ceiling.

---

## Slide 4 — Guardrails and Human Review

**Guardrail results (test split):**

- Human review rate: 6.81% (target ≤15%) ✓
- PII redacted rate: 26.70% ✓
- Auto-routed accuracy: 100% (178 tickets)
- Flagged accuracy: 76.92% (13 tickets)
- Share of all errors caught: 100% (3 of 3)
- Fallback rate: 0.00%

**How guardrails work:**
1. Redact PII (email, phone, API keys, cards, SSN, IP) — before any classifier
2. Flag vague/short tickets for human review
3. Fall back to rules if LLM unavailable

**Speaker notes:**
- Every test-split error is caught by guardrails; auto-routed tickets are perfect.
- PII never reaches the LLM — verified by regression test test_llm_receives_no_pii.
- Rules-only mode (--no-llm) keeps the pipeline running without an API key.

---

## Slide 5 — Error Analysis

**Test split: only 3 errors total**

| Class | Baseline F1 | LLM F1 | Change |
|-------|-------------|--------|--------|
| Product team | 0.793 | 1.000 | +20.7 points |
| Account security | 1.000 | 0.947 | -5.3 points |
| Bug | 0.941 | 1.000 | +5.9 points |
| How-to | 0.897 | 0.955 | +5.8 points |

**Root causes:**
- Product: rules confused feature requests with how-to; LLM distinguishes intent.
- Account access: "how to reset 2FA" triggers how-to keywords; LLM follows surface keywords over intent.

**Speaker notes:**
- Biggest win: product team (+20.7 points) — rules couldn't separate feature requests from how-to.
- Biggest loss: account security (-5.3 points) — "how do I" phrasing confuses the LLM.
- Only 3 errors on test split; small-sample caveat applies.

---

## Slide 6 — Limitations

**Unmet target:** LLM improvement +1.6 points (Issue) and +6.0 points (Team) on synthetic data — below the 10-point acceptance target. Baseline already near-ceiling; target unchanged in requirements.md.

**Small samples:** test n=191, challenge n=39 — results are directional, not proof.

**Urgency derived from issue type**, not independently labeled.

**Challenge-set team routing flat** (+0.1 points): account security drops to 0.600 F1 on Roman-Urdu/ambiguous tickets.

**Speaker notes:**
- Be honest: the 10-point target wasn't met on synthetic data. The challenge set shows the LLM's real advantage emerges with noise.
- Recommend testing on real/noisy production data before deployment.

---

## Slide 7 — Decisions and Trade-offs

**Decisions:**
- OpenAI-compatible API via OPENAI_API_KEY + --base-url flag (OpenRouter default)
- Rules-only fallback (--no-llm) so the pipeline runs without a key
- PII redacted before any classifier (fix commit 18b0ad6)
- Vague-ticket guardrail flags short/ambiguous tickets for review

**Trade-offs:**
- Higher recall (catch all errors) → more human review (6.81%)
- Rules baseline is interpretable but plateaus on synthetic data
- LLM costs more per ticket but handles paraphrase better

**Speaker notes:**
- Privacy first: PII redacted before LLM — non-negotiable.
- Human-in-the-loop: vague tickets go to review, not auto-routed.
- Fallback design: system degrades gracefully to rules, never fails silently.

---

## Slide 8 — Next Steps and 10x Scale

**Next steps:**
- Add few-shot examples for account access vs how-to boundary
- Refine system prompt: "account access issues are NOT how-to even if phrased as questions"
- Test on real/noisy production data where keyword overlap is higher
- Larger test set with bootstrapped confidence intervals

**10x scale:**
- Batch LLM calls with concurrency limits
- Cache TTL/LRU eviction for cost control
- Multi-label tickets (one ticket, multiple issue types)
- Confidence calibration (temperature scaling)

**Speaker notes:**
- The 10-point target gap is a data problem, not a model problem — real noise widens the LLM edge.
- Scale considerations: cost, caching, multi-label support before production rollout.
