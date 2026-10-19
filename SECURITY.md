# Application Security Policy & Threat Model — ScamShield AI

This document establishes the security boundaries, threat model, input sanitization policies, and vulnerability prevention controls for ScamShield AI.

---

## 1. System Assets & Trust Boundaries

```text
  [ Untrusted Zone: Public Users / External Clients ]
                          |
                   (HTTP Requests)
                          v
  ================== TRUST BOUNDARY ==================
    FastAPI Gateway & Pydantic Validation Filter
      - Payload length caps (Text <= 10KB, URL <= 2KB)
      - Content-type enforcement (application/json)
      - Sanitization & normalization
  ====================================================
                          |
  [ Internal Enclave: Core Analysis Engines ]
      - Text Classifier (TF-IDF + Scikit-Learn)
      - URL Lexical Analyzer (100% Offline / Zero Network)
      - Verdict Arbiter (Deterministic Decision Matrix)
                          |
  ====================================================
  [ Ephemeral Response Formatter (Zero Persistence) ]
                          |
                          v
  [ Client Browser: DOM textContent Rendering Only ]
```

### Identified Core Assets
1. **Host Infrastructure:** Windows development/execution environment and underlying OS resources.
2. **Analysis Pipeline Availability:** Freedom from denial-of-service, algorithmic complexity attacks, and process crashes.
3. **User Privacy:** Ephemeral inspection of user-submitted texts and links without unauthorized leakage or logging.

---

## 2. Threat Modeling & Mitigation Matrix (STRIDE)

| Threat Category | Specific Attack Vector | Potential Impact | Enforced Mitigation in ScamShield AI |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Attacker impersonates legitimate brand in subdomains or display text. | User misled into trusting phishing site. | Lexical brand-matching flags brand names positioned in subdomains or non-canonical paths. |
| **Tampering** | Parameter manipulation, injection payloads (`<script>`, SQL fragments) in input fields. | XSS or injection in backend/frontend. | Strict Pydantic string validation; frontend uses `element.textContent`; zero raw `eval()` or database execution. |
| **Repudiation** | Client submits malicious text and claims server generated it. | Disputed results. | Deterministic responses; clear responsible-use disclaimers on every output. |
| **Information Disclosure** | Leakage of submitted personal messages, passwords, or PII via server logs or error traces. | Privacy violation. | PII masking in logs (truncating/hashing inputs > 20 chars); generic error messages (no stack traces to client). |
| **Denial of Service (DoS)** | Giant input buffers (megabyte strings), ReDoS via catastrophic regex backtracking. | Memory exhaustion, thread blockage. | Hard payload limits (Text: 10,000 chars, URL: 2,048 chars); linear-time parsing; no nested greedy regexes. |
| **Elevation of Privilege** | Server-Side Request Forgery (SSRF) where server fetches user-submitted internal or external URL. | Internal network reconnaissance, AWS metadata theft, attacker callback. | **Strict Zero-Fetch URL Policy:** Zero network sockets, zero DNS queries, zero HTTP requests to submitted URLs. |

---

## 3. Strict SSRF Prevention: Zero-Fetch URL Architecture

Many security scanning tools suffer from severe Server-Side Request Forgery (SSRF) vulnerabilities because they attempt to fetch HTTP headers, take screenshots, or follow redirects of submitted URLs.

**ScamShield AI Architectural Guarantee:**
1. The server **NEVER** initiates an HTTP, HTTPS, FTP, WebSocket, or TCP socket connection to any user-submitted link.
2. The server **NEVER** performs DNS name resolution (e.g., `socket.gethostbyname`) on user-submitted domains, preventing DNS rebinding and out-of-band telemetry exfiltration.
3. URL analysis is strictly **lexical and structural**:
   - `urllib.parse.urlsplit` breaks down the string into components (`scheme`, `netloc`, `path`, `query`).
   - String algorithms compute entropy, count character frequencies, match regexes, and inspect TLD registries entirely in local CPU memory.

---

## 4. Input Sanitization & Validation Controls

### 4.1 Request Size Boundaries
- **Message Text:** Maximum 10,000 characters. Sufficient for extended email/SMS messages while preventing buffer exhaustion.
- **URL String:** Maximum 2,048 characters. Matches maximum Internet Explorer/standard browser URL lengths.
- **Payload Rejection:** Any request with both fields empty or containing exclusively whitespace is rejected with HTTP 422 Unprocessable Entity.

### 4.2 Cross-Site Scripting (XSS) Prevention
- In the Vanilla JavaScript frontend (`app/static/js/app.js`), all dynamic text outputs, detected keywords, and verdicts are inserted into the DOM strictly via:
  ```javascript
  element.textContent = data.verdict; // Safe: no HTML parsing
  ```
- HTML injection payloads such as `<script>alert(1)</script>` or `<img src=x onerror=alert(1)>` are treated as literal text characters and cannot execute.

---

## 5. Privacy, Data Minimization & Safe Logging

1. **Zero Data Retention:** User inputs are processed in volatile memory and immediately garbage-collected upon response completion. No file or database persistence is maintained.
2. **Safe Logging Standards:**
   - Any log statements capturing requests must truncate and sanitize inputs:
     ```python
     masked_text = text[:15] + "... [TRUNCATED]" if len(text) > 15 else text
     logger.info(f"Analyzed submission snippet: {masked_text}")
     ```
   - Passwords, credit card numbers, OTPs, or personal identity numbers detected in strings are never written to disk or terminal stdout.

---

## 6. Secret Management & Dependency Hygiene

1. **No Hardcoded Secrets:** No API keys, passwords, or private signing keys exist in the repository.
2. **Environment Isolation:** Configuration is managed via `app/config.py` reading standard environment variables.
3. **Minimal Dependency Footprint:** By avoiding bloated frameworks and extraneous libraries, ScamShield AI reduces supply-chain attack surfaces. Pinned dependencies in `requirements.txt` prevent unexpected breaking changes or compromised upstream updates.

---

## 7. Responsible-Use Limitations & Disclaimers

ScamShield AI is developed as an assistive, educational, and preliminary screening tool for the KLE BCA Coding Club Challenge.
- It does **not** replace enterprise security suites, endpoint detection and response (EDR), or personal judgment.
- Output labels (`likely safe`, `needs review`, `likely scam`) are probabilistic assessments.
- The system must never be used as the sole basis for legal accusations or punitive actions.
