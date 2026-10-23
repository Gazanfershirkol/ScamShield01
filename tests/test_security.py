"""
Security Validation & Hardening Test Suite — ScamShield AI

Validates critical security boundaries and guarantees:
1. SSRF Immunity: Guaranteed zero socket/DNS/network calls during URL analysis.
2. XSS Resilience: Safe handling of script/injection tags and verifying DOM safety.
3. Payload Boundary Defense: Strict rejection of oversized payloads (Text > 10,000, URL > 2,048).
4. ReDoS Resilience: Protection against catastrophic regex backtracking.
5. Path Traversal Defense: Static asset serving sandboxed against directory traversal.
6. Injection Neutrality: SQL/Command injection strings handled strictly as benign/suspicious text.
7. Unicode & Null Byte Sanitization: Malformed encodings and control characters handled gracefully.
"""

import socket
import time
import urllib.request
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Provides TestClient instance for API security testing."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. SSRF Immunity & Zero-Network Verification
# -----------------------------------------------------------------------------

def test_security_ssrf_zero_network_calls(client, monkeypatch):
    """
    Submitting AWS metadata, localhost, or external URLs must NEVER trigger
    outbound socket connections, HTTP requests, or DNS resolution.
    """
    def forbidden_dns(host, *args, **kwargs):
        raise AssertionError(f"CRITICAL SECURITY VIOLATION: DNS lookup for '{host}' attempted during analysis!")

    def forbidden_http(*args, **kwargs):
        raise AssertionError("CRITICAL SECURITY VIOLATION: Outbound HTTP call attempted during analysis!")

    orig_getaddrinfo = socket.getaddrinfo

    def safe_getaddrinfo(host, port, *args, **kwargs):
        # Allow internal asyncio loopback resolution, block all external or target host lookups
        if host and host not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError(f"CRITICAL SECURITY VIOLATION: DNS resolution of '{host}' attempted!")
        return orig_getaddrinfo(host, port, *args, **kwargs)

    orig_connect = socket.socket.connect

    def safe_connect(self, address):
        host, port = address[0], address[1]
        # Any target port outside the internal loopback pipe or any non-localhost host is forbidden
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError(f"CRITICAL SECURITY VIOLATION: Outbound connection to '{host}:{port}' attempted!")
        if port in (80, 8080, 443, 22, 9000, 5000):
            raise AssertionError(f"CRITICAL SECURITY VIOLATION: SSRF attempt to internal service '{host}:{port}'!")
        return orig_connect(self, address)

    monkeypatch.setattr(socket, "gethostbyname", forbidden_dns)
    monkeypatch.setattr(socket, "getaddrinfo", safe_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", safe_connect)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden_http)

    malicious_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8080/admin",
        "http://localhost:22",
        "http://[::1]:80/",
        "http://internal-vault.corp.local/secret",
        "https://external-phishing-host.xyz/collect",
    ]

    for target_url in malicious_targets:
        response = client.post(
            "/api/v1/analyze",
            json={"url": target_url, "text": "Verify your identity here"}
        )
        assert response.status_code == 200, f"Analysis failed on {target_url}"
        data = response.json()
        assert data["url_analysis"]["provided"] is True



# -----------------------------------------------------------------------------
# 2. XSS Resilience & Safe Handling
# -----------------------------------------------------------------------------

def test_security_xss_payload_resilience(client):
    """
    Notorious XSS payloads must be accepted as raw text and returned safely
    without triggering 500 errors or backend corruption.
    """
    xss_vectors = [
        "<script>alert('XSS')</script>",
        '"><svg/onload=alert(String.fromCharCode(88,83,83))>',
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<iframe src=\"javascript:alert('xss')\"></iframe>",
    ]

    for vector in xss_vectors:
        response = client.post(
            "/api/v1/analyze",
            json={"text": f"Your account is locked. Click here {vector}", "url": "http://example.xyz"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] in ("likely safe", "needs review", "likely scam")


def test_security_frontend_no_unsafe_user_innerhtml():
    """
    Audits the frontend app.js to verify untrusted user text or URLs are never
    interpolated into innerHTML.
    """
    app_js_path = settings.STATIC_DIR / "js" / "app.js"
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # Verify that textContent is used for user content rendering
    assert "textContent" in content
    # Verify no dangerous direct assignments of raw user input to innerHTML
    assert "innerHTML = data.text" not in content
    assert "innerHTML = data.url" not in content
    assert "innerHTML = text" not in content
    assert "innerHTML = url" not in content


# -----------------------------------------------------------------------------
# 3. Payload Boundary Controls
# -----------------------------------------------------------------------------

def test_security_payload_size_boundaries(client):
    """Verify strict rejection of inputs exceeding defined buffer limits."""
    # Text boundary: exactly 10,000 characters is allowed
    exact_text = "A" * settings.MAX_TEXT_LENGTH
    res_exact = client.post("/api/v1/analyze", json={"text": exact_text})
    assert res_exact.status_code == 200

    # Text boundary: 10,001 characters is rejected with 422
    too_long_text = "A" * (settings.MAX_TEXT_LENGTH + 1)
    res_too_long = client.post("/api/v1/analyze", json={"text": too_long_text})
    assert res_too_long.status_code == 422

    # URL boundary: exactly 2,048 characters is allowed
    exact_url = "http://example.com/" + ("b" * (settings.MAX_URL_LENGTH - 19))
    assert len(exact_url) == settings.MAX_URL_LENGTH
    res_url_exact = client.post("/api/v1/analyze", json={"url": exact_url})
    assert res_url_exact.status_code == 200

    # URL boundary: 2,049 characters is rejected with 422
    too_long_url = "http://example.com/" + ("b" * (settings.MAX_URL_LENGTH - 18))
    assert len(too_long_url) == settings.MAX_URL_LENGTH + 1
    res_url_too_long = client.post("/api/v1/analyze", json={"url": too_long_url})
    assert res_url_too_long.status_code == 422


# -----------------------------------------------------------------------------
# 4. ReDoS (Regular Expression Denial of Service) Resilience
# -----------------------------------------------------------------------------

def test_security_redos_resilience(client):
    """
    Submitting strings designed to trigger exponential regex backtracking
    must complete in microsecond/millisecond time without CPU lockup.
    """
    # Pre-warm client to avoid counting one-time initialization against execution time
    client.post("/api/v1/analyze", json={"text": "warmup test", "url": "http://safe-site.com"})

    pathological_strings = [
        "a" * 2000 + "!",
        "http://" + ("sub." * 150) + "domain.com",
        "verify " * 300,
        "!" * 1500,
    ]

    for p_str in pathological_strings:
        start_time = time.perf_counter()
        response = client.post(
            "/api/v1/analyze",
            json={"text": p_str, "url": "http://safe-site.com"}
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert response.status_code == 200
        # ReDoS would cause multi-second or minute freezes; ensure linear microsecond execution
        assert elapsed_ms < 500.0, f"Potential ReDoS detected: took {elapsed_ms:.1f}ms on payload"


# -----------------------------------------------------------------------------
# 5. Path Traversal Defense
# -----------------------------------------------------------------------------

def test_security_path_traversal_prevention(client):
    """
    Attempting directory traversal attacks via static files route must fail safely
    with 404 or 400 without leaking source code or system files.
    """
    traversal_paths = [
        "/static/../../etc/passwd",
        "/static/..%2f..%2fetc/passwd",
        "/static/../../windows/system32/cmd.exe",
        "/static/../../app/config.py",
        "/static/../../../requirements.txt",
    ]

    for path in traversal_paths:
        response = client.get(path)
        # StaticFiles returns 404 for paths that resolve outside directory
        assert response.status_code in (404, 400), f"Path traversal succeeded on {path}"


# -----------------------------------------------------------------------------
# 6. SQL & Command Injection Neutrality
# -----------------------------------------------------------------------------

def test_security_injection_neutrality(client):
    """
    SQL and command injection patterns must be handled harmlessly as pure text
    without server-side execution or uncaught errors.
    """
    injection_strings = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "UNION SELECT null, username, password FROM users--",
        "$(whoami)",
        "; cat /etc/passwd",
        "| ping -n 5 127.0.0.1",
        "& echo %PATH%",
    ]

    for inj in injection_strings:
        response = client.post(
            "/api/v1/analyze",
            json={"text": f"Alert: {inj} is your security code.", "url": None}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["risk_score"], int)


# -----------------------------------------------------------------------------
# 7. Unicode & Control Character Sanitization
# -----------------------------------------------------------------------------

def test_security_unicode_and_null_bytes(client):
    """
    Malformed encodings, null bytes, zero-width characters, and RTL overrides
    must be handled without unhandled 500 exceptions.
    """
    weird_inputs = [
        "Your account\x00has been locked", # Null byte
        "Verify at http://example.com/\u202e/moc.elpmaxe//:ptth", # RTL override
        "U\u200br\u200bg\u200be\u200bn\u200bt notice", # Zero-width spaces
        "😀🚀⚠️🔒💯" * 50, # Emoji flood
    ]

    for inp in weird_inputs:
        response = client.post(
            "/api/v1/analyze",
            json={"text": inp, "url": "http://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] in ("likely safe", "needs review", "likely scam")


# -----------------------------------------------------------------------------
# 8. Trusted Proxy & Client-IP Boundary Verification (Stage A Security)
# -----------------------------------------------------------------------------

def _make_mock_request(headers=None, client_host="127.0.0.1", client_port=50000):
    """Constructs a lightweight Starlette Request with specific client host and headers."""
    from starlette.requests import Request
    raw_headers = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode("latin-1"), str(v).encode("latin-1")))
    client = (client_host, client_port) if client_host is not None else None
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/analyze",
        "headers": raw_headers,
        "client": client,
    }
    return Request(scope)


def test_client_ip_direct_untrusted_ignores_forwarded_headers():
    """
    Direct untrusted peer cannot spoof IP: client-supplied X-Forwarded-For
    and X-Real-IP are strictly ignored when direct peer is not in TRUSTED_PROXIES.
    """
    from app.api.endpoints import extract_client_ip

    # Direct connection from public IP not in trusted proxies
    req = _make_mock_request(
        headers={
            "X-Forwarded-For": "1.1.1.1",
            "X-Real-IP": "2.2.2.2",
        },
        client_host="203.0.113.10",
    )
    extracted = extract_client_ip(req, trusted_proxies={"127.0.0.1", "::1", "testclient"})
    assert extracted == "203.0.113.10"


def test_client_ip_trusted_proxy_single_client():
    """
    When direct peer is a trusted proxy, legitimate client IP from X-Forwarded-For
    is extracted and validated.
    """
    from app.api.endpoints import extract_client_ip

    req = _make_mock_request(
        headers={"X-Forwarded-For": "198.51.100.50"},
        client_host="127.0.0.1",
    )
    extracted = extract_client_ip(req, trusted_proxies={"127.0.0.1"})
    assert extracted == "198.51.100.50"


def test_client_ip_trusted_proxy_x_real_ip():
    """
    When direct peer is trusted and X-Forwarded-For is absent, X-Real-IP is honored if valid.
    """
    from app.api.endpoints import extract_client_ip

    req = _make_mock_request(
        headers={"X-Real-IP": "198.51.100.77"},
        client_host="127.0.0.1",
    )
    extracted = extract_client_ip(req, trusted_proxies={"127.0.0.1"})
    assert extracted == "198.51.100.77"


def test_client_ip_multi_hop_proxy_chain_safe_extraction():
    """
    Multi-hop proxy chain: walks right-to-left through trusted proxies
    and identifies the authentic untrusted client boundary.
    """
    from app.api.endpoints import extract_client_ip

    # Architecture: Client (198.51.100.25) -> Cloudflare (10.0.0.1) -> Nginx (127.0.0.1) -> ScamShield
    trusted = {"127.0.0.1", "10.0.0.1"}
    req = _make_mock_request(
        headers={"X-Forwarded-For": "198.51.100.25, 10.0.0.1"},
        client_host="127.0.0.1",
    )
    extracted = extract_client_ip(req, trusted_proxies=trusted)
    assert extracted == "198.51.100.25"


def test_client_ip_leftmost_spoofing_prevented():
    """
    Blind leftmost trust prevention:
    If an attacker injects a spoofed IP into X-Forwarded-For before hitting a reverse proxy,
    the proxy appends the real client IP. Right-to-left traversal picks the real client IP,
    rejecting the forged leftmost value.
    """
    from app.api.endpoints import extract_client_ip

    # Attacker at 198.51.100.42 injects '8.8.8.8' as X-Forwarded-For.
    # Proxy at 127.0.0.1 appends real client IP: '8.8.8.8, 198.51.100.42'.
    req = _make_mock_request(
        headers={"X-Forwarded-For": "8.8.8.8, 198.51.100.42"},
        client_host="127.0.0.1",
    )
    extracted = extract_client_ip(req, trusted_proxies={"127.0.0.1"})
    # Must NOT blindly return 8.8.8.8
    assert extracted == "198.51.100.42"


def test_client_ip_malformed_headers_safe_fallback():
    """
    Malformed IP values, non-IP strings, and header injection attempts
    must fail validation safely and fall back to direct peer without 500 crashes.
    """
    from app.api.endpoints import extract_client_ip

    malformed_vectors = [
        "not-an-ip-address",
        "999.999.999.999",
        "<script>alert(1)</script>",
        "127.0.0.1; rm -rf /",
        "203.0.113.1, invalid_hop",
        "",
    ]
    for vector in malformed_vectors:
        req = _make_mock_request(
            headers={"X-Forwarded-For": vector, "X-Real-IP": vector},
            client_host="127.0.0.1",
        )
        extracted = extract_client_ip(req, trusted_proxies={"127.0.0.1"})
        assert extracted == "127.0.0.1"


def test_client_ip_missing_client_never_maps_to_localhost():
    """
    Unknown or absent socket peer must return 'unknown' and NEVER silently map to localhost.
    """
    from app.api.endpoints import extract_client_ip

    req_none_client = _make_mock_request(client_host=None)
    assert extract_client_ip(req_none_client) == "unknown"

    req_empty_host = _make_mock_request(client_host="")
    assert extract_client_ip(req_empty_host) == "unknown"


def test_client_ip_cidr_subnet_matching():
    """
    Trusted proxies configured as CIDR subnets (e.g. 10.0.0.0/8, 172.16.0.0/12)
    correctly match peer IPs within the subnet and reject outside IPs.
    """
    from app.api.endpoints import is_trusted_proxy

    trusted_cidrs = {"10.0.0.0/8", "172.16.0.0/12", "127.0.0.1"}

    assert is_trusted_proxy("10.1.2.3", trusted_cidrs) is True
    assert is_trusted_proxy("10.254.254.254", trusted_cidrs) is True
    assert is_trusted_proxy("172.16.5.1", trusted_cidrs) is True
    assert is_trusted_proxy("172.31.255.255", trusted_cidrs) is True
    assert is_trusted_proxy("127.0.0.1", trusted_cidrs) is True

    # Outside CIDR ranges
    assert is_trusted_proxy("172.32.0.1", trusted_cidrs) is False
    assert is_trusted_proxy("192.168.1.1", trusted_cidrs) is False
    assert is_trusted_proxy("203.0.113.1", trusted_cidrs) is False


def test_rate_limit_bypass_prevention_via_spoofed_headers(client):
    """
    Attack simulation: Untrusted client attempting to bypass rate limits
    by rotating forged X-Forwarded-For headers.
    Because the direct peer is untrusted, all requests hit the same rate-limit bucket
    and the attack is throttled with HTTP 429.
    """
    from app.services.rate_limiter import rate_limiter

    rate_limiter.reset()

    # Configure TRUSTED_PROXIES so 'testclient' is NOT trusted for this test
    from app.api.endpoints import extract_client_ip
    from app.config import settings

    # Simulate 65 requests from an untrusted peer rotating forged headers
    peer_ip = "198.51.100.99"
    untrusted_proxies = {"127.0.0.1", "::1"} # 'testclient' is NOT in here

    responses = []
    for i in range(65):
        req = _make_mock_request(
            headers={"X-Forwarded-For": f"1.2.3.{i+1}"},
            client_host=peer_ip,
        )
        ip = extract_client_ip(req, trusted_proxies=untrusted_proxies)
        # Verify forged header was discarded
        assert ip == peer_ip
        allowed, retry_after = rate_limiter.is_allowed(ip)
        responses.append(allowed)

    # First 60 requests allowed, remaining 5 blocked
    assert sum(responses[:60]) == 60
    assert sum(responses[60:]) == 0
    assert not responses[60]

    rate_limiter.reset()

