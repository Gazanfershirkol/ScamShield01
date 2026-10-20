"""
ScamShield AI — Passive Lexical URL Analysis Engine

This module implements 100% passive, offline, zero-network structural and lexical
evaluation of user-submitted URLs. It operates strictly in local memory with
guaranteed immunity against Server-Side Request Forgery (SSRF).
"""

from dataclasses import dataclass, field
import ipaddress
import math
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlsplit


@dataclass
class URLAnalysisResult:
    """Structured result returned by the passive URL analyzer."""
    provided: bool = False
    risk_score: int = 0
    target_domain: str = ""
    is_ip_address: bool = False
    has_homoglyphs: bool = False
    flagged_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize result to a dictionary matching the API contract."""
        return {
            "provided": self.provided,
            "risk_score": self.risk_score,
            "target_domain": self.target_domain,
            "is_ip_address": self.is_ip_address,
            "has_homoglyphs": self.has_homoglyphs,
            "flagged_indicators": self.flagged_indicators,
        }


# -----------------------------------------------------------------------------
# Heuristic Dictionaries & Configuration Constants
# -----------------------------------------------------------------------------

HIGH_RISK_TLDS: Set[str] = {
    ".xyz", ".top", ".click", ".buzz", ".rest", ".cfd", ".surf",
    ".icu", ".cam", ".live", ".online", ".site", ".club", ".work",
    ".party", ".gq", ".ml", ".cf", ".tk", ".ga"
}

POPULAR_BRANDS: List[str] = [
    "paypal", "sbi", "hdfc", "icici", "apple", "google", "microsoft",
    "amazon", "netflix", "whatsapp", "facebook", "instagram", "paytm",
    "phonepe", "binance", "coinbase", "chase", "wellsfargo", "citi",
    "indiatimes", "flipkart", "irctc"
]

SUSPICIOUS_PATH_KEYWORDS: List[str] = [
    "login", "signin", "verify", "verification", "account", "update",
    "banking", "kyc", "wallet", "authenticate", "password", "security",
    "confirm", "claim", "refund", "re-activate", "unblock"
]

TRUSTED_CANONICAL_DOMAINS: Set[str] = {
    "google.com", "microsoft.com", "apple.com", "amazon.com", "github.com",
    "wikipedia.org", "youtube.com", "linkedin.com", "gov.in", "nic.in",
    "edu", "ac.in"
}


# -----------------------------------------------------------------------------
# Metric & Feature Extraction Helpers
# -----------------------------------------------------------------------------

def calculate_shannon_entropy(text: str) -> float:
    """
    Computes Shannon entropy (information density) for a string.
    High entropy in domain names often indicates Algorithmically Generated Domains (DGA)
    or random hex strings used by attackers.
    """
    if not text:
        return 0.0
    freq: Dict[str, int] = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    entropy = 0.0
    text_len = len(text)
    for count in freq.values():
        p = count / text_len
        entropy -= p * math.log2(p)
    return entropy


def is_valid_ip(hostname: str) -> bool:
    """Checks whether the hostname is an IPv4 or IPv6 address."""
    # Strip brackets from IPv6 hostnames like [::1]
    clean_host = hostname.strip("[]")
    try:
        ipaddress.ip_address(clean_host)
        return True
    except ValueError:
        return False


def is_trusted_canonical(hostname: str) -> bool:
    """
    Checks if hostname matches or is an authentic subdomain of a known
    reputable domain (e.g., mail.google.com -> trusted).
    """
    clean_host = hostname.lower()
    for trusted in TRUSTED_CANONICAL_DOMAINS:
        if clean_host == trusted or clean_host.endswith("." + trusted):
            return True
    return False


# -----------------------------------------------------------------------------
# Core URL Analysis Engine
# -----------------------------------------------------------------------------

def analyze_url(url: Optional[str]) -> URLAnalysisResult:
    """
    Performs purely offline, lexical, and structural analysis of a URL string.
    Never executes HTTP, DNS, or socket calls.

    Returns:
        URLAnalysisResult with integer risk score (0-100) and flagged indicators.
    """
    if not url or not url.strip():
        return URLAnalysisResult(provided=False, risk_score=0)

    url_str = url.strip()
    flagged: List[str] = []
    score = 0

    # Handle missing scheme gracefully (e.g. "example.com/login" -> assume "http://")
    has_explicit_scheme = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url_str))
    parse_target = url_str if has_explicit_scheme else f"http://{url_str}"

    try:
        parts = urlsplit(parse_target)
    except Exception as e:
        return URLAnalysisResult(
            provided=True,
            risk_score=60,
            target_domain="malformed",
            flagged_indicators=[f"Malformed URL structure could not be parsed: {str(e)[:50]}"]
        )

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.lower()
    query = parts.query.lower()

    # Netloc may contain credentials like "user:pass@host"
    if "@" in netloc:
        score += 35
        flagged.append("Embedded credentials detected ('@' symbol obscures actual destination host)")
        # Split out userinfo to inspect host
        netloc = netloc.split("@")[-1]

    # Port stripping (e.g., host:8080)
    hostname = netloc.split(":")[0] if ":" in netloc else netloc

    # If hostname could not be resolved from parser
    if not hostname:
        flagged.append("Malformed URL: Hostname could not be extracted")
        return URLAnalysisResult(
            provided=True,
            risk_score=50,
            target_domain="",
            flagged_indicators=flagged
        )

    # 1. IP Address Host Check (+45)
    ip_host = is_valid_ip(hostname)
    if ip_host:
        score += 45
        flagged.append("Host is a raw IP address (legitimate services rarely serve web portals via raw IP)")

    # 2. Homoglyph & Punycode Check (+30)
    has_homoglyphs = False
    if "xn--" in hostname:
        has_homoglyphs = True
        score += 30
        flagged.append("Punycode prefix detected ('xn--') indicating potential Internationalized Domain Name spoofing")
    elif any(ord(char) > 127 for char in hostname):
        has_homoglyphs = True
        score += 30
        flagged.append("Non-ASCII unicode characters detected in domain (potential visual homoglyph spoof)")

    # 3. High-Risk TLD Check (+20)
    matched_tld = None
    for tld in HIGH_RISK_TLDS:
        if hostname.endswith(tld):
            matched_tld = tld
            break

    if matched_tld:
        score += 20
        flagged.append(f"High-risk top-level domain detected ('{matched_tld}') frequently abused for disposable phishing")

    # 4. Brand Impersonation in Subdomain (+35)
    subdomain_parts = hostname.split(".")
    domain_labels = [p for p in subdomain_parts if p]

    # Find the effective root domain (e.g., "example.com" or "paypal.com")
    root_domain = ".".join(domain_labels[-2:]) if len(domain_labels) >= 2 else hostname

    for brand in POPULAR_BRANDS:
        # Check if brand is in subdomains but not in root domain
        # e.g., paypal.com.verify-account.net -> brand is "paypal", root is "verify-account.net"
        if len(domain_labels) > 2:
            subdomain_prefix = ".".join(domain_labels[:-2])
            if brand in subdomain_prefix and brand not in root_domain:
                score += 35
                flagged.append(
                    f"Brand impersonation detected: Known brand '{brand}' placed in subdomain while root is '{root_domain}'"
                )
                break
        # Also check deceptive compound root domain (e.g. "secure-paypal-login.xyz")
        elif brand in root_domain and not root_domain.startswith(brand + "."):
            # Check if brand is mixed with deceptive keywords
            for kw in ["secure", "update", "verify", "login", "bank", "account", "support", "help"]:
                if kw in root_domain and kw != brand:
                    score += 30
                    flagged.append(
                        f"Deceptive brand keyword combination detected in domain ('{brand}', '{kw}')"
                    )
                    break

    # 5. Suspicious Path Keywords (+15)
    matched_path_keywords = []
    combined_path_query = f"{path}?{query}"
    for kw in SUSPICIOUS_PATH_KEYWORDS:
        if kw in combined_path_query:
            matched_path_keywords.append(kw)

    if matched_path_keywords:
        score += 15
        flagged.append(
            f"Suspicious credential/financial keywords detected in URL path: {', '.join(matched_path_keywords[:3])}"
        )

    # 6. Excessive Subdomain Depth (+15)
    # e.g. login.secure.account.update.bank.com (depth >= 4 levels)
    if len(domain_labels) > 3:
        score += 15
        flagged.append(f"Excessive subdomain depth detected ({len(domain_labels)} label levels)")

    # 7. Shannon Entropy on Domain Label (+15)
    # Exclude common TLD from entropy to measure root label randomness
    root_label = domain_labels[-2] if len(domain_labels) >= 2 else domain_labels[0]
    domain_entropy = calculate_shannon_entropy(root_label)
    if domain_entropy > 3.8 and len(root_label) >= 8:
        score += 15
        flagged.append(
            f"High domain label Shannon entropy ({domain_entropy:.2f} bits) indicating potential algorithmic generation (DGA)"
        )

    # 8. Insecure HTTP with Sensitive Keywords (+20)
    if scheme == "http" and matched_path_keywords:
        score += 20
        flagged.append("Insecure plain HTTP protocol used with sensitive credential path keywords")

    # 9. Clean Canonical Domain Safeguard (-30 points)
    if is_trusted_canonical(hostname):
        score -= 30
        flagged.append(f"Domain '{hostname}' recognized on trusted canonical baseline list (safeguard applied)")

    # 10. Clamp final risk score between 0 and 100
    final_score = max(0, min(100, score))

    # If no flags triggered, add reassuring note
    if not flagged:
        flagged.append("No alarming lexical or structural indicators observed in submitted URL")

    return URLAnalysisResult(
        provided=True,
        risk_score=final_score,
        target_domain=hostname,
        is_ip_address=ip_host,
        has_homoglyphs=has_homoglyphs,
        flagged_indicators=flagged
    )
