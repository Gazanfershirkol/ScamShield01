"""
ScamShield AI — Phase 4 Text Analyzer Test Suite

Verifies:
- High-risk phishing urgency detection
- Benign personal & academic message classification
- Top explainability token extraction
- Empty and whitespace input handling
- 10,000 character maximum boundary execution
- Specialized scam categories (KYC, utility cutoff, job fraud)
"""

from pathlib import Path
import pytest
from app.services.text_analyzer import analyze_text, TextAnalysisResult


def test_text_high_risk_urgency():
    """Verify that aggressive financial urgency yields high risk score (>= 80)."""
    text = "URGENT: Your bank account will be closed in 2 hours. Send OTP immediately."
    result = analyze_text(text)

    assert result.provided is True
    assert result.risk_score >= 80
    assert result.probability >= 0.80
    assert any("urgency" in pattern.lower() for pattern in result.detected_patterns)


def test_text_benign_message():
    """Verify that ordinary personal communication yields low risk score (<= 20)."""
    text = "Hey, are we still meeting for lunch at 1 PM today?"
    result = analyze_text(text)

    assert result.provided is True
    assert result.risk_score <= 20
    assert result.probability <= 0.20


def test_text_explainability_tokens():
    """Verify that key explainable tokens are extracted from high-risk messages."""
    text = "URGENT: Your bank account will be closed in 2 hours. Send OTP immediately."
    result = analyze_text(text)

    assert result.provided is True
    assert len(result.key_tokens) > 0
    # At least one of the prominent alarm tokens should appear
    token_str = " ".join(result.key_tokens).lower()
    assert any(tok in token_str for tok in ["urgent", "otp", "bank", "immediately", "account", "closed"])


def test_text_empty_and_whitespace():
    """Verify that empty, None, and whitespace inputs return provided=False and score=0."""
    res_none = analyze_text(None)
    assert res_none.provided is False
    assert res_none.risk_score == 0

    res_empty = analyze_text("")
    assert res_empty.provided is False
    assert res_empty.risk_score == 0

    res_whitespace = analyze_text("   \n\t   ")
    assert res_whitespace.provided is False
    assert res_whitespace.risk_score == 0


def test_text_max_length_boundary():
    """Verify that submitting a string of exactly 10,000 characters executes without error."""
    long_text = ("This is a normal message about our semester project. " * 200)[:10000]
    assert len(long_text) == 10000

    result = analyze_text(long_text)
    assert result.provided is True
    assert isinstance(result.risk_score, int)
    assert 0 <= result.risk_score <= 100


def test_text_electricity_cutoff_scam():
    """Verify detection of power disconnection scam."""
    text = "Dear consumer, your electricity power will be disconnected tonight at 9:30 PM. Call electricity officer immediately."
    result = analyze_text(text)

    assert result.provided is True
    assert result.risk_score >= 75


def test_text_task_job_scam():
    """Verify detection of work-from-home Telegram task scam."""
    text = "Earn Rs 5,000 daily from home! Part-time online job liking YouTube videos. Contact HR on WhatsApp now."
    result = analyze_text(text)

    assert result.provided is True
    assert result.risk_score >= 75


def test_text_academic_college_notice():
    """Verify benign classification of college academic notification."""
    text = "KLE BCA Department Announcement: Coding club meeting today at 3 PM in Computer Lab 2. All students attend."
    result = analyze_text(text)

    assert result.provided is True
    assert result.risk_score <= 25
