import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baseline_classifier import classify_ticket, ISSUE_TYPE_KEYWORDS, TEAM_KEYWORDS
from guardrails import redact_pii, GuardrailPipeline


def test_baseline_classifier():
    # Test billing
    result = classify_ticket("Invoice question", "I was charged $49.99 but my plan shows $29.99")
    assert result.issue_type == "billing"
    assert result.team == "billing"
    assert result.confidence > 0.5
    
    # Test bug
    result = classify_ticket("App crash", "The app crashes with NullPointerException at line 245")
    assert result.issue_type == "bug"
    assert result.team == "tech support"
    
    # Test account access
    result = classify_ticket("Password reset", "I'm not receiving the password reset email")
    assert result.issue_type == "account access"
    assert result.team == "account security"
    
    print("✓ Baseline classifier tests passed")


def test_pii_redaction():
    text = "Contact me at user@example.com or call +1-555-123-4567. My API key is sk_test_abcdefghijklmnopqrstuvwxyz"
    redacted, was_redacted = redact_pii(text)
    assert was_redacted
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted
    assert "[API_KEY]" in redacted
    assert "user@example.com" not in redacted
    assert "+1-555-123-4567" not in redacted
    
    # Test no PII
    text2 = "This is a normal ticket without any sensitive info"
    redacted2, was_redacted2 = redact_pii(text2)
    assert not was_redacted2
    assert redacted2 == text2
    
    print("✓ PII redaction tests passed")


def test_guardrails_pipeline():
    # Test without LLM (rules only)
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    result = pipe.classify_with_guardrails("Invoice question", "I was charged $49.99 but my plan shows $29.99")
    assert result.issue_type == "billing"
    assert result.team == "billing"
    assert result.fallback_used == False  # Not using LLM, so not a fallback
    assert result.human_review == False  # High confidence
    
    # Test low confidence triggers human review
    pipe_low = GuardrailPipeline(confidence_threshold=0.99, llm_classifier=None, use_llm=False)
    result = pipe_low.classify_with_guardrails("Random text", "This doesn't match any keywords well")
    assert result.human_review == True
    
    print("✓ Guardrails pipeline tests passed")


def test_keyword_maps():
    # Verify all required classes have keywords
    required_issue_types = {"billing", "bug", "account access", "feature request", "how-to", "outage"}
    required_teams = {"billing", "tech support", "account security", "product"}
    
    assert set(ISSUE_TYPE_KEYWORDS.keys()) == required_issue_types
    assert set(TEAM_KEYWORDS.keys()) == required_teams
    
    # Each should have at least 5 keywords
    for keywords in ISSUE_TYPE_KEYWORDS.values():
        assert len(keywords) >= 5
    for keywords in TEAM_KEYWORDS.values():
        assert len(keywords) >= 5
    
    print("✓ Keyword map tests passed")


if __name__ == "__main__":
    test_baseline_classifier()
    test_pii_redaction()
    test_guardrails_pipeline()
    test_keyword_maps()
    print("\n✅ All tests passed!")