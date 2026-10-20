"""
ScamShield AI — Phase 3 URL Analyzer Test Suite

Verifies passive zero-network lexical and structural heuristics:
- Raw IP address hostnames
- Homoglyphs and Punycode spoofing
- Embedded credential deception ('@')
- High-risk / disposable TLDs
- Brand impersonation in subdomains
- Trusted canonical domain safeguards
- Graceful handling of malformed inputs
- Zero outbound network socket / DNS calls (SSRF prevention)
"""

import socket
import urllib.request
import pytest
from app.services.url_analyzer import analyze_url, URLAnalysisResult, calculate_shannon_entropy


def test_url_ip_address_host():
    """Verify that raw IPv4 addresses are flagged as high risk (+45)."""
    result = analyze_url("http://192.168.1.1/login")
    assert result.provided is True
    assert result.is_ip_address is True
    assert result.risk_score >= 45
    assert any("IP address" in indicator for indicator in result.flagged_indicators)


def test_url_homoglyph_punycode():
    """Verify that punycode 'xn--' domains are flagged (+30)."""
    result = analyze_url("http://xn--pypal-4ve.com")
    assert result.provided is True
    assert result.has_homoglyphs is True
    assert result.risk_score >= 30
    assert any("Punycode" in indicator for indicator in result.flagged_indicators)


def test_url_embedded_credentials():
    """Verify that '@' symbol credential obfuscation is flagged (+35)."""
    result = analyze_url("http://legit.com@phishing-site.xyz/login")
    assert result.provided is True
    assert result.risk_score >= 35
    assert any("Embedded credentials" in indicator for indicator in result.flagged_indicators)


def test_url_high_risk_tld():
    """Verify that known disposable / high-abuse TLDs are flagged (+20)."""
    result = analyze_url("http://secure-verify.click")
    assert result.provided is True
    assert result.risk_score >= 20
    assert any(".click" in indicator for indicator in result.flagged_indicators)


def test_url_brand_in_subdomain():
    """Verify that brand names placed in subdomains are flagged as impersonation (+35)."""
    result = analyze_url("http://paypal.com.verify-account.net")
    assert result.provided is True
    assert result.risk_score >= 35
    assert any("Brand impersonation" in indicator for indicator in result.flagged_indicators)


def test_url_safe_canonical_domain():
    """Verify that recognized benign canonical domains yield low risk (< 15)."""
    result = analyze_url("https://www.google.com")
    assert result.provided is True
    assert result.risk_score <= 15
    assert result.is_ip_address is False
    assert result.has_homoglyphs is False


def test_url_malformed_string():
    """Verify that malformed or bizarre URLs do not crash the parser."""
    result = analyze_url("htp:/invalid..url/%%something")
    assert result.provided is True
    assert isinstance(result.risk_score, int)
    assert 0 <= result.risk_score <= 100


def test_url_empty_and_whitespace():
    """Verify that empty, None, or blank inputs return provided=False and score=0."""
    res_none = analyze_url(None)
    assert res_none.provided is False
    assert res_none.risk_score == 0

    res_empty = analyze_url("")
    assert res_empty.provided is False
    assert res_empty.risk_score == 0

    res_spaces = analyze_url("   \n\t  ")
    assert res_spaces.provided is False
    assert res_spaces.risk_score == 0


def test_shannon_entropy_calculation():
    """Verify Shannon entropy computation for uniform vs repetitive strings."""
    # Repetitive single character has zero entropy
    assert calculate_shannon_entropy("aaaaaaa") == 0.0
    # Random-like alphanumeric string has high entropy
    entropy_high = calculate_shannon_entropy("7b9f2c8d1e4a")
    assert entropy_high > 3.0


def test_zero_network_calls_guarantee(monkeypatch):
    """
    CRITICAL SECURITY TEST: Asserts that under NO circumstances does
    analyze_url initiate a socket connection or HTTP request (SSRF Immunity).
    """
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("SECURITY VIOLATION: Socket opened during passive URL analysis!")

    def forbidden_urlopen(*args, **kwargs):
        raise AssertionError("SECURITY VIOLATION: HTTP request initiated during passive URL analysis!")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    monkeypatch.setattr(socket, "gethostbyname", forbidden_socket)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)

    # Analyze various URLs including private IPs and external URLs
    test_urls = [
        "http://127.0.0.1:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://evil-attacker.xyz/exploit",
        "https://www.google.com/search?q=test"
    ]

    for u in test_urls:
        result = analyze_url(u)
        assert isinstance(result, URLAnalysisResult)
        assert 0 <= result.risk_score <= 100
