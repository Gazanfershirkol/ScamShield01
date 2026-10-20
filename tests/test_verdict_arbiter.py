"""
Unit Tests for ScamShield AI — Verdict Arbiter & Evidence Synthesis Engine
"""

import pytest

from app.config import settings
from app.services.text_analyzer import TextAnalysisResult
from app.services.url_analyzer import URLAnalysisResult
from app.services.verdict_arbiter import (
    UnifiedVerdict,
    VerdictArbiter,
    synthesize_verdict,
    verdict_arbiter,
)


@pytest.fixture
def arbiter():
    """Provides a fresh VerdictArbiter instance with default settings."""
    return VerdictArbiter()


def test_arbiter_both_high_risk(arbiter):
    """Both text and URL score > 80 -> verdict must strictly be 'likely scam'."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=85,
        probability=0.88,
        detected_patterns=["Urgency language", "Credential demand"],
        key_tokens=["immediately", "locked", "verify"],
    )
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=92,
        target_domain="secure-bank-login.xyz",
        is_ip_address=False,
        has_homoglyphs=False,
        flagged_indicators=["High-risk TLD .xyz", "Target keyword 'login'"],
    )

    verdict = arbiter.synthesize(text_res, url_res)

    assert verdict.verdict == "likely scam"
    assert verdict.risk_score >= settings.VERDICT_SCAM_THRESHOLD
    assert verdict.confidence >= 0.75
    assert len(verdict.evidence) >= 2
    assert "Do not open" in verdict.recommended_action
    assert verdict.text_analysis["provided"] is True
    assert verdict.url_analysis["provided"] is True


def test_arbiter_both_low_risk(arbiter):
    """Both text and URL score < 20 -> verdict must strictly be 'likely safe'."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=10,
        probability=0.08,
        detected_patterns=[],
        key_tokens=[],
    )
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=5,
        target_domain="docs.python.org",
        is_ip_address=False,
        has_homoglyphs=False,
        flagged_indicators=[],
    )

    verdict = arbiter.synthesize(text_res, url_res)

    assert verdict.verdict == "likely safe"
    assert verdict.risk_score < settings.VERDICT_REVIEW_THRESHOLD
    assert verdict.confidence < 0.35
    assert len(verdict.evidence) >= 1
    assert "routine digital hygiene" in verdict.recommended_action.lower()


def test_arbiter_conflicting_signals(arbiter):
    """
    Safe text + high-risk URL -> verdict escalates to 'needs review' or 'likely scam'.
    Security-first policy ensures dangerous links are never masked by benign text.
    """
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=12,
        probability=0.10,
        detected_patterns=[],
        key_tokens=[],
    )
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=95,
        target_domain="account-verify.cfd",
        is_ip_address=False,
        has_homoglyphs=False,
        flagged_indicators=["High-risk TLD .cfd", "Brand impersonation"],
    )

    verdict = arbiter.synthesize(text_res, url_res)

    # 95 * 0.85 = 80.75 -> blended score = 81 -> 'likely scam'
    assert verdict.verdict in ("needs review", "likely scam")
    assert verdict.risk_score >= 75
    assert any("divergent threat levels" in e or "Link security" in e for e in verdict.evidence)


def test_arbiter_text_only(arbiter):
    """Valid text + unprovided URL -> evaluates text score correctly."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=80,
        probability=0.82,
        detected_patterns=["Threat of legal action"],
        key_tokens=["warrant", "arrest"],
    )

    verdict = arbiter.synthesize(text_res, None)

    assert verdict.risk_score == 80
    assert verdict.verdict == "likely scam"
    assert verdict.text_analysis["provided"] is True
    assert verdict.url_analysis["provided"] is False
    assert "message text" in verdict.summary.lower()


def test_arbiter_url_only(arbiter):
    """Valid URL + unprovided text -> evaluates URL score correctly."""
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=60,
        target_domain="track-order.top",
        is_ip_address=False,
        has_homoglyphs=False,
        flagged_indicators=["High-risk TLD .top"],
    )

    verdict = arbiter.synthesize(None, url_res)

    assert verdict.risk_score == 60
    assert verdict.verdict == "needs review"
    assert verdict.text_analysis["provided"] is False
    assert verdict.url_analysis["provided"] is True
    assert "destination link" in verdict.summary.lower() or "link formatting" in verdict.summary.lower()


def test_arbiter_critical_override_ip_address(arbiter):
    """Raw IP address with credential keywords triggers critical scam override."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=40,
        probability=0.45,
        detected_patterns=["Credential demand"],
        key_tokens=["login", "verify"],
    )
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=55,
        target_domain="192.168.1.1",
        is_ip_address=True,
        has_homoglyphs=False,
        flagged_indicators=["URL host is a raw IP address"],
    )

    verdict = arbiter.synthesize(text_res, url_res)

    # Escalated to at least scam threshold
    assert verdict.verdict == "likely scam"
    assert verdict.risk_score >= settings.VERDICT_SCAM_THRESHOLD


def test_arbiter_divergence_escalation(arbiter):
    """Moderate text score (0) and URL score (52) triggers divergence escalation to 'needs review'."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=0,
        probability=0.01,
        detected_patterns=[],
        key_tokens=[],
    )
    url_res = URLAnalysisResult(
        provided=True,
        risk_score=52,
        target_domain="promo-sale.club",
        is_ip_address=False,
        has_homoglyphs=False,
        flagged_indicators=["High-risk TLD .club"],
    )

    verdict = arbiter.synthesize(text_res, url_res)

    assert verdict.risk_score >= settings.VERDICT_REVIEW_THRESHOLD
    assert verdict.verdict == "needs review"


def test_arbiter_empty_inputs_raises_value_error(arbiter):
    """Synthesizing without text or URL must raise ValueError."""
    with pytest.raises(ValueError, match="both text and URL analyses are empty"):
        arbiter.synthesize(None, None)

    unprovided_text = TextAnalysisResult(provided=False)
    unprovided_url = URLAnalysisResult(provided=False)
    with pytest.raises(ValueError, match="both text and URL analyses are empty"):
        arbiter.synthesize(unprovided_text, unprovided_url)


def test_arbiter_confidence_calculation(arbiter):
    """Confidence must strictly equal round(risk_score / 100.0, 2)."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=67,
        probability=0.67,
        detected_patterns=["Uncommon request"],
        key_tokens=["urgent"],
    )
    verdict = arbiter.synthesize(text_res, None)

    assert verdict.risk_score == 67
    assert verdict.confidence == 0.67


def test_arbiter_to_dict_format(arbiter):
    """Serialized verdict dictionary must match the expected API JSON schema."""
    text_res = TextAnalysisResult(
        provided=True,
        risk_score=78,
        probability=0.80,
        detected_patterns=["Financial urgency"],
        key_tokens=["payment", "penalty"],
    )
    verdict = arbiter.synthesize(text_res, None)
    data = verdict.to_dict()

    expected_keys = {
        "verdict",
        "risk_score",
        "confidence",
        "summary",
        "text_analysis",
        "url_analysis",
        "evidence",
        "recommended_action",
        "analyzed_at",
    }
    assert expected_keys.issubset(data.keys())
    assert isinstance(data["evidence"], list)
    assert isinstance(data["summary"], str)
    assert isinstance(data["recommended_action"], str)


def test_functional_convenience_function():
    """Verify synthesize_verdict() functional helper behaves identically to singleton."""
    text_res = TextAnalysisResult(provided=True, risk_score=25, probability=0.25)
    result = synthesize_verdict(text_res, None)

    assert isinstance(result, UnifiedVerdict)
    assert result.verdict == "likely safe"
    assert result.risk_score == 25
