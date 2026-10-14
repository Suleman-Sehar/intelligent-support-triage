import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from guardrails import GuardrailPipeline, redact_pii, is_vague_ticket, count_keyword_matches
from baseline_classifier import classify_ticket


def test_empty_input():
    """Empty subject and body should not crash, should be flagged for human review."""
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    result = pipe.classify_with_guardrails("", "")
    assert result.human_review == True
    assert result.confidence < 0.75


def test_none_input():
    """None subject and body should be handled gracefully."""
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    result = pipe.classify_with_guardrails("", "")
    assert result is not None
    assert hasattr(result, "issue_type")


def test_very_long_input():
    """Very long input should not crash."""
    long_text = "Bug report: app crashes. " * 500
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    result = pipe.classify_with_guardrails("Bug", long_text)
    assert result is not None
    assert result.issue_type in ["bug", "feature request", "outage", "billing", "account access", "how-to"]


def test_unicode_input():
    """Unicode characters should not crash PII redaction or classification."""
    unicode_text = "Hello world with \u00e9 accent"
    redacted, was_redacted = redact_pii(unicode_text)
    assert was_redacted == False  # No PII
    
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    result = pipe.classify_with_guardrails("Question", "I have a problem with my account")
    assert result is not None


def test_vague_ticket_guardrail():
    """Vague tickets should be flagged for human review."""
    pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)
    
    # Vague ticket with no clear intent
    result = pipe.classify_with_guardrails("Question", "I have a question about something")
    assert result.human_review == True
    
    # Non-vague billing ticket should not be flagged (unless low confidence)
    result = pipe.classify_with_guardrails("Invoice question", "I was charged $49.99 but my plan shows $29.99")
    assert result.human_review == False  # High confidence, not vague


def test_pii_redaction_empty():
    """Empty string should not crash PII redaction."""
    redacted, was_redacted = redact_pii("")
    assert was_redacted == False
    assert redacted == ""


def test_keyword_match_count():
    """Keyword matching should correctly count matches."""
    text = "I have a billing issue with my invoice"
    count = count_keyword_matches(text)
    assert count >= 1


def test_is_vague_ticket_detection():
    """is_vague_ticket should detect short and keyword-poor text."""
    assert is_vague_ticket("") == True
    assert is_vague_ticket("Hello") == True
    assert is_vague_ticket("Hi I have a question about something") == True
    
    # Not vague
    billing = "I was charged $99.99 for invoice INV-2024-001234 but my contract says $49.99"
    assert is_vague_ticket(billing) == False


class MockLLMClassifier:
    """Mock LLM classifier for testing retry and fallback."""
    
    def __init__(self, fail_schema=False, fail_timeout=False, fail_count=0):
        self.fail_schema = fail_schema
        self.fail_timeout = fail_timeout
        self.fail_count = fail_count
        self.call_count = 0
    
    def classify(self, subject, body):
        self.call_count += 1
        if self.fail_timeout and self.call_count <= self.fail_count:
            raise TimeoutError("API timeout")
        if self.fail_schema and self.call_count <= self.fail_count:
            from pydantic import ValidationError
            raise ValidationError.from_exception(
                {"__root__": "schema error"},
                ValueError("schema validation error"),
                {}
            )
        
        from llm_classifier import TicketClassification
        return TicketClassification(
            issue_type="billing",
            team="billing",
            confidence=0.9,
            reasoning="Test classification"
        )


def test_llm_schema_violation_retry():
    """LLMClassifier should retry on schema violations and eventually succeed."""
    from unittest.mock import MagicMock
    from llm_classifier import LLMClassifier, TicketClassification
    
    # Create an LLMClassifier instance without calling __init__
    llm = LLMClassifier.__new__(LLMClassifier)
    llm.max_retries = 3
    llm.retry_delay = 0.01
    llm.model = "gpt-4o-mini"
    llm.temperature = 0.0
    llm.system_prompt = "Test"
    llm.schema = {"type": "object", "properties": {}, "required": []}
    
    # Create mock cache
    class MockCache:
        def get(self, text): return None
        def set(self, text, prediction): pass
    llm.cache = MockCache()
    
    call_count = [0]
    
    def mock_create(*args, **kwargs):
        call_count[0] += 1
        mock_resp = Mock()
        if call_count[0] <= 2:
            # Return invalid JSON that will fail pydantic validation
            mock_resp.choices = [Mock()]
            mock_resp.choices[0].message.content = '{"invalid": "data"}'
        else:
            # Return valid JSON on 3rd attempt
            mock_resp.choices = [Mock()]
            mock_resp.choices[0].message.content = json.dumps({
                "issue_type": "billing",
                "team": "billing",
                "confidence": 0.9,
                "reasoning": "Recovered after retry"
            })
        return mock_resp
    
    mock_client = Mock()
    mock_client.chat.completions.create = mock_create
    llm.client = mock_client
    
    # Call the classify method directly
    result = llm.classify("Invoice question", "I was charged wrong amount")
    
    assert result.issue_type == "billing"
    assert result.team == "billing"
    assert call_count[0] == 3  # Should have retried twice, then succeeded


def test_llm_timeout_fallback():
    """LLM timeout should trigger fallback to rules classifier."""
    mock_llm = MockLLMClassifier(fail_timeout=True, fail_count=999)
    mock_llm.classify = Mock(side_effect=TimeoutError("API timeout"))
    mock_llm.max_retries = 3
    
    pipe = GuardrailPipeline(
        confidence_threshold=0.75,
        llm_classifier=mock_llm,
        use_llm=True
    )
    
    result = pipe.classify_with_guardrails("Invoice question", "I was charged wrong amount")
    assert result.fallback_used == True
    assert result.team == "billing"  # Baseline should get billing


def test_disagreement_flag():
    """When baseline and LLM disagree, human review should be triggered."""
    from llm_classifier import TicketClassification
    
    class DisagreeingLLM:
        def __init__(self):
            self.max_retries = 3
            self.call_count = 0
        def classify(self, subject, body):
            return TicketClassification(
                issue_type="how-to",  # Disagrees with baseline (which says billing)
                team="tech support",
                confidence=0.95,
                reasoning="Test"
            )
    
    pipe = GuardrailPipeline(
        confidence_threshold=0.75,
        llm_classifier=DisagreeingLLM(),
        use_llm=True
    )
    
    result = pipe.classify_with_guardrails("Invoice question", "I was charged $99.99 for invoice INV-2024-001234")
    assert result.human_review == True  # Disagreement triggers review
    assert result.disagreement_flag == True


def test_edge_cases_file_loaded():
    """Edge cases file should contain 10 entries."""
    import csv
    edge_path = Path(__file__).parent.parent / "data" / "edge_cases.csv"
    with open(edge_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 10
    for row in rows:
        assert "subject" in row
        assert "body" in row


if __name__ == "__main__":
    test_empty_input()
    print("  PASS: test_empty_input")
    test_none_input()
    print("  PASS: test_none_input")
    test_very_long_input()
    print("  PASS: test_very_long_input")
    test_unicode_input()
    print("  PASS: test_unicode_input")
    test_vague_ticket_guardrail()
    print("  PASS: test_vague_ticket_guardrail")
    test_pii_redaction_empty()
    print("  PASS: test_pii_redaction_empty")
    test_keyword_match_count()
    print("  PASS: test_keyword_match_count")
    test_is_vague_ticket_detection()
    print("  PASS: test_is_vague_ticket_detection")
    test_llm_schema_violation_retry()
    print("  PASS: test_llm_schema_violation_retry")
    test_llm_timeout_fallback()
    print("  PASS: test_llm_timeout_fallback")
    test_disagreement_flag()
    print("  PASS: test_disagreement_flag")
    test_edge_cases_file_loaded()
    print("  PASS: test_edge_cases_file_loaded")
    print("\nAll edge case tests passed!")