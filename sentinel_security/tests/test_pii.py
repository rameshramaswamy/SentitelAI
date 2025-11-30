# sentinel_security/tests/test_pii.py
import pytest
from src.core.pii_scrubber import PIIScrubber

@pytest.fixture
def scrubber():
    return PIIScrubber()

def test_email_redaction(scrubber):
    text = "Please contact support@sentinel.ai for help."
    cleaned = scrubber.scrub(text)
    assert "support@sentinel.ai" not in cleaned
    assert "[REDACTED_EMAIL]" in cleaned

def test_phone_redaction(scrubber):
    text = "My number is 555-123-4567, call me."
    cleaned = scrubber.scrub(text)
    assert "555-123-4567" not in cleaned
    assert "[REDACTED_PHONE]" in cleaned
    
    # Test with parenthesis
    text2 = "Or (555) 123-4567"
    cleaned2 = scrubber.scrub(text2)
    assert "[REDACTED_PHONE]" in cleaned2

def test_credit_card_redaction(scrubber):
    # Visa-like pattern
    text = "Here is my card: 4111 1111 1111 1111 charge it."
    cleaned = scrubber.scrub(text)
    assert "4111 1111 1111 1111" not in cleaned
    assert "[REDACTED_CC]" in cleaned
    
    # Compact pattern
    text2 = "4111111111111111"
    cleaned2 = scrubber.scrub(text2)
    assert "[REDACTED_CC]" in cleaned2

def test_mixed_content(scrubber):
    text = "Email bob@gmail.com or call 987-654-3210 regarding card 1234-5678-9012-3456"
    cleaned = scrubber.scrub(text)
    assert "[REDACTED_EMAIL]" in cleaned
    assert "[REDACTED_PHONE]" in cleaned
    assert "[REDACTED_CC]" in cleaned
    assert "bob@gmail.com" not in cleaned