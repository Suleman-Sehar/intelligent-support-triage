#!/usr/bin/env python3
"""
Live demo script for Intelligent Support Triage.
Run this during presentation to show real-time classification.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from guardrails import GuardrailPipeline, redact_pii
from llm_classifier import LLMClassifier, PredictionCache
from baseline_classifier import classify_ticket as baseline_classify


def demo_pii_redaction():
    print("=" * 60)
    print("DEMO 1: PII Redaction (runs before LLM)")
    print("=" * 60)
    
    ticket = """Subject: Billing issue with my account
Body: Hi, I was charged $99.99 for invoice INV-2024-001234 but my contract says $49.99.
My email is sarah.johnson@company.com and phone is +1-555-123-4567.
Also my API key sk_test_FAKE_KEY_PLACEHOLDER_1234567890 was exposed in logs.
Please help!"""
    
    print("\nORIGINAL:")
    print(ticket)
    
    redacted, was_redacted = redact_pii(ticket)
    
    print(f"\nREDACTED (PII found: {was_redacted}):")
    print(redacted)
    
    print("\n[OK] Email, phone, API key all redacted before LLM sees them")


def demo_classification():
    print("\n" + "=" * 60)
    print("DEMO 2: Ticket Classification with Guardrails")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] No OPENAI_API_KEY set - running in FALLBACK MODE (rules only)")
        print("   Set OPENAI_API_KEY to see LLM classification\n")
        llm = None
        use_llm = False
    else:
        cache = PredictionCache("cache")
        llm = LLMClassifier(base_url="https://openrouter.ai/api/v1", cache=cache)
        use_llm = True
        print(f"[OK] LLM loaded: gpt-4o-mini via OpenRouter\n")
    
    pipe = GuardrailPipeline(
        confidence_threshold=0.75,
        llm_classifier=llm,
        use_llm=use_llm
    )
    
    # Test tickets
    test_cases = [
        {
            "name": "Billing Discrepancy",
            "subject": "Invoice question",
            "body": "I was charged $99.99 for invoice INV-2024-001234 but my contract says $49.99. Can you explain?"
        },
        {
            "name": "Bug Report",
            "subject": "App crashes on export",
            "body": "The app crashes every time I click 'Export Report'. Error: NullPointerException at line 245 in ReportExporter.java"
        },
        {
            "name": "Account Access - 2FA",
            "subject": "Lost authenticator app",
            "body": "I lost my phone with the authenticator app. Need to reset 2FA for account admin@company.com. Urgent!"
        },
        {
            "name": "Feature Request",
            "subject": "Dark mode request",
            "body": "Please add dark mode toggle. Current light theme causes eye strain during night shifts."
        },
        {
            "name": "How-To Question",
            "subject": "Slack integration setup",
            "body": "How do I connect the Slack integration? Documentation is unclear about webhook URLs."
        },
        {
            "name": "Outage Report",
            "subject": "API returning 500 errors",
            "body": "API returning 500 errors for /v1/tickets endpoint since 14:00 UTC. All our automations are failing."
        },
    ]
    
    for tc in test_cases:
        print(f"\n--- {tc['name']} ---")
        print(f"Subject: {tc['subject']}")
        print(f"Body: {tc['body'][:80]}...")
        
        result = pipe.classify_with_guardrails(tc['subject'], tc['body'])
        
        print(f"  Issue Type: {result.issue_type}")
        print(f"  Team:       {result.team}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  PII Redacted: {result.pii_redacted}")
        print(f"  Human Review: {result.human_review}")
        print(f"  Fallback Used: {result.fallback_used}")
        print(f"  Reasoning: {result.reasoning[:80]}...")


def demo_fallback():
    print("\n" + "=" * 60)
    print("DEMO 3: Fallback Behavior (--no-llm flag)")
    print("=" * 60)
    
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    
    result = pipe.classify_with_guardrails(
        "Payment failed", 
        "My credit card was declined but I have sufficient funds. Please retry."
    )
    
    print(f"\nRules-only classification:")
    print(f"  Issue: {result.issue_type}, Team: {result.team}, Confidence: {result.confidence:.2%}")
    print(f"  Fallback: {result.fallback_used} (expected: False since LLM disabled)")
    print(f"  Human Review: {result.human_review}")


def demo_low_confidence():
    print("\n" + "=" * 60)
    print("DEMO 4: Low Confidence -> Human Review")
    print("=" * 60)
    
    pipe = GuardrailPipeline(confidence_threshold=0.99, llm_classifier=None, use_llm=False)
    
    result = pipe.classify_with_guardrails(
        "Random inquiry", 
        "Hello, I have a question about something maybe related to my account or billing or whatever."
    )
    
    print(f"\nLow-confidence ticket (threshold=0.99):")
    print(f"  Issue: {result.issue_type}, Team: {result.team}, Confidence: {result.confidence:.2%}")
    print(f"  Human Review: {result.human_review} <-- FLAGGED FOR HUMAN")


if __name__ == "__main__":
    print("INTELLIGENT SUPPORT TRIAGE - LIVE DEMO")
    print("=" * 60)
    
    demo_pii_redaction()
    demo_classification()
    demo_fallback()
    demo_low_confidence()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. PII redacted BEFORE LLM call")
    print("  2. Structured output with confidence + reasoning")
    print("  3. Human review queue for low confidence")
    print("  4. Automatic fallback when LLM unavailable")
    print("  5. Reproducible: python demo.py")