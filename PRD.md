# Product Requirements Document (PRD) — ScamShield AI

## 1. Problem Statement & Background
- **Competition:** KLE's BCA Coding Club — Interdepartmental Challenge
- **Department Track:** AI / ML
- **Problem Statement Code:** AI · 03 — AI Scam & Phishing Detector
- **Project Name:** ScamShield AI
- **Context:** Everyday digital users (students, elderly individuals, employees, non-technical consumers) face a relentless surge of digital fraud delivered through SMS, email, messaging apps (WhatsApp, Telegram), and social media. Phishing attacks and social engineering lures trick users into credential theft, financial extortion, identity compromise, and malware downloads.
- **Problem:** Existing security solutions are either enterprise-heavy (expensive mail gateways), opaque (browser warnings with no explanation), or high-friction (requiring user accounts, telemetry tracking, or complex installations). Users lack a fast, explainable, lightweight second opinion that diagnoses suspect messages and suspicious links without violating their privacy.

## 2. Target Users & Personas
1. **Primary: Everyday Digital Citizen / Student / Novice User**
   - *Needs:* Simple paste-and-check interface; plain-English verdict; clear explanation of *why* a message or link is dangerous; actionable advice on what to do next.
   - *Pain Points:* Confused by technical jargon (e.g., "DMARC failure", "punycode mismatch"); anxious about whether a bank alert or job offer is real.
2. **Secondary: Peer Reviewer / Department Evaluator / Hackathon Judge**
   - *Needs:* Objective evaluation metrics (Precision, Recall, F1); reproducible validation; API access for automated testing; visible architecture discipline.
3. **Tertiary: Small Developer / Bot Integrator**
   - *Needs:* Clean REST API contract (`POST /api/v1/analyze`) to integrate scam detection into local chatbots or email filters.

## 3. Goals, Non-Goals & Assumptions

### 3.1 Goals
- Accept message text, a URL, or both simultaneously.
- Return one of three unambiguous verdict labels: `likely safe`, `needs review`, or `likely scam`.
- Compute an overall normalized Risk Score from 0 to 100 (and 0.0 to 1.0 scale).
- Provide human-understandable evidence: specific detected keywords, urgent phrasing patterns, lexical URL anomalies, and structural indicators.
- Expose a fully functional REST API with interactive documentation (OpenAPI / Swagger).
- Provide a responsive, accessible, professional web dashboard with zero framework bloat.
- Provide a rigorous, reproducible evaluation pipeline with Precision, Recall, F1-score, Confusion Matrix, and detailed False Positive / False Negative analysis.
- Maintain complete user privacy: perform offline/local inference with zero outbound requests to submitted URLs.

### 3.2 Non-Goals (Out of Scope for Hackathon MVP)
- **Zero Network Navigation:** The tool will *never* fetch, scrape, crawl, or resolve submitted URLs over HTTP/HTTPS/DNS.
- **No User Accounts / Authentication:** No login, registration, password hashing, or user profile management.
- **No Database Persistence:** Analysis is ephemeral in memory; no storing of user submissions or sensitive personal messages.
- **No External LLM API Dependency:** No OpenAI, Claude, or third-party paid API calls. The core model must run locally and deterministically.
- **No Blockchain / Crypto integrations:** No tokens, ledgers, or Web3 components.
- **No Browser Extension / Mobile App:** Focus is exclusively on a clean web client and REST API.

### 3.3 Assumptions
- The host system runs Windows 10/11 with Python 3.10+ (or will have Python installed prior to Phase 1 implementation).
- Evaluators will run the app locally on `http://127.0.0.1:8000`.
- Dataset will use curated open-source public benchmark datasets (e.g., SMS Spam Collection, Phishing URL feeds) combined with synthetic edge cases.

## 4. User Journeys

### Journey 1: Dual Input Analysis (Message + URL)
1. User lands on ScamShield AI dashboard.
2. User pastes an SMS: *"URGENT: Your State Bank account is suspended. Verify KYC immediately at http://sbi-kyc-update.xyz/login to avoid penalties."*
3. User clicks **Analyze Message & Link**.
4. The system validates inputs, runs the text model and URL heuristic engine in parallel, synthesizes a unified verdict.
5. UI displays:
   - Verdict: **Likely Scam** (Crimson badge with warning icon).
   - Risk Score: **92 / 100**.
   - Evidence Summary: Detected urgency triggers ("URGENT", "suspended", "avoid penalties"), credential harvesting lure ("KYC"), non-official domain mimicking a bank, abnormal top-level domain (`.xyz`), presence of credential target keywords in URL path.
   - Actionable Guidance: *"Do not click the link. Contact your bank through official phone numbers."*

### Journey 2: URL-Only Quick Check
1. User receives an unfamiliar link in a chat group: `https://free-recharge-offer.gift-reward5.com/claim`.
2. User leaves text empty, pastes URL into the URL input, clicks **Analyze Link**.
3. System runs lexical URL feature extraction and structural risk scoring.
4. UI presents verdict `likely scam` with identified red flags (hyphenated subdomain deception, high entropy, prize lure).

### Journey 3: Text-Only Scam Detection
1. User receives a recruitment message without a link offering 50,000 INR/day for liking YouTube videos.
2. User pastes the text, leaves URL blank, clicks **Analyze Message**.
3. System extracts linguistic n-grams, computes classification score, flags advance-fee and task scam markers, returning `likely scam`.

### Journey 4: Developer / Judge API Evaluation
1. Evaluator sends a `POST` request to `/api/v1/analyze` with JSON payload `{"text": "...", "url": "..."}`.
2. API validates schema and responds with HTTP 200 within < 50ms containing structured verdict, score, breakdown, and timestamp.
3. Evaluator queries `/api/v1/evaluation` to review cross-validated benchmark metrics (Precision, Recall, F1, Confusion Matrix).

## 5. Functional Requirements (FR)

### Mandatory Competition Features
- **FR-01: Flexible Input Modalities:** System MUST accept message text alone, a URL alone, or both text and URL together. System MUST reject empty submissions with an informative prompt.
- **FR-02: Standardized Three-State Verdict:** System MUST categorize each analyzed submission into exactly one of three verdicts:
  1. `likely safe` (Low risk: typical transactional or normal personal communication, benign domain).
  2. `needs review` (Moderate risk: borderline patterns, mixed signals, benign message with unknown URL, or promotional urgency without malicious payload).
  3. `likely scam` (High risk: aggressive social engineering, known phishing indicators, brand spoofing, or deceptive link structure).
- **FR-03: Normalized Risk Score:** System MUST compute an integer risk score `0–100` alongside a float `0.00–1.00`.
- **FR-04: Understandable Evidence Breakdown:** System MUST return clear, non-technical explanatory bullet points highlighting:
  - Textual cues (urgency, threats, financial lures, credential demands, impersonation).
  - URL cues (domain spoofing, suspicious TLD, excessive subdomains, IP hostnames, homoglyphs/punycode, target keywords).
  - Synthesis explanation describing how the final verdict was reached.
- **FR-05: REST API:** System MUST expose:
  - `POST /api/v1/analyze`: Core analysis endpoint.
  - `GET /api/v1/health`: System health and model readiness check.
  - `GET /api/v1/evaluation`: Summary of benchmark model metrics and validation results.
- **FR-06: Scientific Evaluation Report:** The project MUST include an automated evaluation module calculating:
  - Precision, Recall, F1-Score (macro and per-class).
  - Confusion Matrix (True Positives, False Positives, True Negatives, False Negatives).
  - Concrete qualitative case studies of False Positives and False Negatives.

## 6. Non-Functional Requirements (NFR)
- **NFR-01: Latency:** End-to-end analysis response time MUST be under 100 milliseconds for text up to 2,000 characters and URLs up to 2,048 characters.
- **NFR-02: Zero Network Side-Effects:** No outbound network calls are made during inference. Submitted URLs are never resolved or pinged.
- **NFR-03: Explainability & Interpretability:** The machine learning classifier must be inspectable (e.g., TF-IDF + linear classifier feature weights) to extract top contributing tokens.
- **NFR-04: Accessibility (WCAG 2.1 AA):** All color-coded verdicts must be accompanied by textual labels and SVG icons. Color contrast ratio must meet minimum 4.5:1 for standard text. Keyboard navigation supported for all controls.
- **NFR-05: Modularity & Portability:** Python code must be clean, PEP 8 compliant, type-annotated (`typing`), and run seamlessly on standard Python 3.10+ without heavy GPU or deep-learning runtimes.
- **NFR-06: Robust Input Validation:** Inputs are bounded: Text maximum 10,000 characters; URL maximum 2,048 characters. Malicious inputs (XSS tags, control characters) must be sanitized before rendering.

## 7. State Specifications

| State | Trigger | System Behavior | User Presentation |
| :--- | :--- | :--- | :--- |
| **Empty State** | Page load / Reset | Input fields blank. Analyze button enabled. Sample preset chips displayed. | Helpful guidance: "Paste a suspicious message, link, or both to evaluate potential fraud." |
| **Loading State** | Analyze triggered | API call in-flight. Inputs disabled. Spinner/shimmer active. | "Analyzing indicators and structural patterns..." (accessible aria-busy). |
| **Success: Likely Safe** | Risk score < 35 | Green badge, check icon, score 0-34, breakdown of benign signals. | "Likely Safe — No common scam indicators detected. Practice standard caution." |
| **Success: Needs Review** | Risk score 35-74 | Amber badge, alert icon, score 35-74, highlighted caution points. | "Needs Review — Contains mixed signals or unusual phrasing. Verify via trusted channels." |
| **Success: Likely Scam** | Risk score ≥ 75 | Crimson badge, shield warning icon, score 75-100, critical indicators list. | "Likely Scam — High-risk patterns detected. Do not click links or share credentials." |
| **Uncertainty State** | Short/vague text or conflicting signals | Returns `needs review` with explicit low-confidence indicator note. | "Confidence Moderate: Insufficient context to guarantee assessment. Exercise prudence." |
| **Validation Error State** | Both fields empty / oversized payload | HTTP 422 / inline UI error message without full page reload. | "Please provide either a message text, a URL, or both (max 10,000 chars)." |
| **Server Error State** | Unhandled exception | HTTP 500 with sanitized error ID. No stack trace shown to user. | "An unexpected error occurred during analysis. Please try again." |

## 8. Privacy, Responsible Use & Disclaimers

### 8.1 Responsible AI Disclaimers (Mandatory in UI & API)
> **DISCLAIMER:** ScamShield AI provides probabilistic and heuristic risk assessments based on pattern recognition. It does **NOT** guarantee that a message is completely safe, nor does it constitute legal or cryptographic proof of fraudulent activity. Always independently verify suspicious communications directly with verified official institutions.

### 8.2 Privacy Protections
- Zero data retention: Submitted texts and URLs are evaluated in volatile RAM and immediately discarded.
- No analytics tracking or telemetry transmitting user contents to third parties.
- URLs are parsed lexically only (zero DNS lookup, zero HTTP requests).

## 9. Acceptance Criteria by Mandatory Feature

| Feature ID | Acceptance Criteria |
| :--- | :--- |
| **AC-01** | User submits text only -> System returns valid verdict, score, text evidence, URL evidence marked "Not provided". |
| **AC-02** | User submits URL only -> System returns valid verdict, score, URL evidence, text evidence marked "Not provided". |
| **AC-03** | User submits text + URL -> System analyzes both, blends scores with explicit policy, returns synthesized evidence. |
| **AC-04** | User submits nothing -> System displays clear validation error and prevents API dispatch. |
| **AC-05** | Verdict is strictly one of `likely safe`, `needs review`, `likely scam`. |
| **AC-06** | Score is strictly an integer between 0 and 100 and a float between 0.00 and 1.00. |
| **AC-07** | Evidence contains at least 1-5 concrete, factual observations (or states "No alarming indicators observed"). |
| **AC-08** | `/api/v1/analyze` accepts JSON and returns expected schema with HTTP 200 within 100ms. |
| **AC-09** | `/api/v1/evaluation` returns verified metrics from the held-out test split. |
| **AC-10** | UI complies with WCAG AA contrast and renders properly on mobile (360px+) and desktop (1280px+). |

## 10. Measurable Hackathon Success Criteria
1. **Functional Completeness:** 100% of mandatory features (text, URL, both, verdict, score, evidence, API, evaluation report) implemented and verified.
2. **Model Performance Target:** Macro F1-score ≥ 0.85 on held-out test dataset with balanced precision and recall.
3. **Inference Latency:** Mean API latency < 50ms across 100 test requests.
4. **Code Quality:** 0 unhandled exceptions on edge cases; 100% type coverage on core modules; automated test suite covering all endpoints and algorithms.
5. **Presentation Value:** Clean, polished, responsive UI with interactive demo presets for live judges.
