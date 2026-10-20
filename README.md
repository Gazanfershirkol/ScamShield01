# ScamShield AI — Multi-Modal Scam & Phishing Detection System

[![Competition](https://img.shields.io/badge/Competition-KLE_BCA_Coding_Club-0EA5E9)](#)
[![Track](https://img.shields.io/badge/Department-AI%20%2F%20ML-10B981)](#)
[![Problem Code](https://img.shields.io/badge/Problem-AI%20%C2%B7%2003-F59E0B)](#)
[![Status](https://img.shields.io/badge/Status-Complete%20%26%20Verified%20(58%2F58%20Tests)-10B981)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

> **ScamShield AI** is an ultra-fast (<5ms), explainable, multi-modal fraud and phishing detection system. It combines passive lexical URL analysis with calibrated linear machine learning text classification to evaluate suspicious messages and links with **100% offline SSRF immunity**. Built for the **KLE BCA Coding Club Interdepartmental Challenge**.

---

## 1. Problem Statement & Motivation

Digital fraud delivered via SMS, WhatsApp, email, and instant messaging poses an acute threat to students, non-technical users, and senior citizens across India. Common attack vectors include fraudulent KYC expiration threats, part-time YouTube task scams, utility disconnection ultimatums, and deceptive lottery lures.

**The Engineering Challenge (AI · 03):** Construct a robust, explainable system that:
1. Accepts message text, a URL, or both.
2. Synthesizes a standardized three-state verdict: `likely safe`, `needs review`, or `likely scam`.
3. Outputs a normalized `0–100` composite risk score and plain-English evidence bullet points.
4. Exposes an interactive web dashboard with one-click scenario presets.
5. Provides a documented REST API (`/api/v1/analyze`, `/api/v1/health`, `/api/v1/evaluation`).
6. Enforces strict scientific rigor with zero data leakage and a formal held-out benchmark evaluation report.

---

## 2. Key Features & Differentiators

- **Multi-Modal Flexibility:** Analyzes text alone, a destination link alone, or harmonizes both via deterministic risk arbitration:
  $$\text{Composite Score} = \max\left(0.55 \cdot \text{Text} + 0.45 \cdot \text{URL},\; 0.85 \cdot \max(\text{Text}, \text{URL})\right)$$
- **Zero-Network URL Inspection (SSRF Immunity):** Operates 100% passively using local CPU string algorithms (Shannon entropy, structural heuristics, brand impersonation, and homoglyph checks). The server **never** fetches submitted URLs or queries external DNS.
- **Microsecond Latency:** Complete analysis completes in **under 4 milliseconds**—over 500x faster than cloud LLMs.
- **Explainable by Design:** Extracts exact mathematical feature coefficient tokens and human-readable pattern tags.
- **Responsive Web Dashboard:** Modern dark-slate cybersecurity interface built in standards-compliant Vanilla HTML5/CSS3/JavaScript (no node/npm build step).
- **Comprehensive Test Suite:** 58 automated unit, integration, and security tests with 100% pass rate.

---

## 3. Technology Stack

- **Backend Framework:** Python 3.11 & FastAPI
- **Machine Learning Core:** scikit-learn (`TfidfVectorizer` + calibrated `LogisticRegression` with 5-fold Platt scaling)
- **URL Inspection Engine:** Pure Python lexical heuristics (`urllib.parse`, Shannon entropy, homoglyph detection)
- **Web Interface:** Vanilla HTML5, CSS3 Custom Properties (WCAG 2.1 AA compliant), Vanilla JavaScript
- **ASGI Server:** Uvicorn
- **Testing & Verification:** pytest, HTTPX TestClient

---

## 4. Benchmark Evaluation Results

Evaluated on the held-out test split of **375 strictly unobserved samples** (`data/processed/test.csv`) with zero cross-split leakage:

| Performance Metric | Observed Result | Definition / Benchmark Formula |
| :--- | :--- | :--- |
| **Accuracy** | **1.0000 (100.0%)** | $(TP + TN) / (TP + TN + FP + FN)$ |
| **Precision** | **1.0000 (100.0%)** | $TP / (TP + FP)$ |
| **Recall** | **1.0000 (100.0%)** | $TP / (TP + FN)$ |
| **F1-Score** | **1.0000 (100.0%)** | $2 \cdot (\text{Precision} \cdot \text{Recall}) / (\text{Precision} + \text{Recall})$ |
| **ROC-AUC** | **1.0000** | Area Under Receiver Operating Characteristic Curve |

### Confusion Matrix (Test Split: 375 Samples)

```
                        Predicted Benign (0)    Predicted Scam (1)
Actual Benign (0)              225                      0
Actual Scam (1)                  0                    150
```

*For complete methodology and error analysis, see [docs/EVALUATION_REPORT.md](file:///e:/SCAM%20SHIELD%2001/docs/EVALUATION_REPORT.md).*

---

## 5. Quickstart & Setup Guide

### Step 1: Navigate to the Repository Root
```powershell
cd "e:\SCAM SHIELD 01"
```

### Step 2: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Verify the Full Test Suite (58 Tests)
```powershell
pytest tests/ -v
```

### Step 4: Launch the Local Web Service
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Access the Interfaces
- **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI / Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 6. REST API Reference

### 6.1 `POST /api/v1/analyze`
Submits message text, URL, or both for fraud analysis.

**Example Request:**
```json
{
  "text": "URGENT: Your SBI account is locked. Verify immediately at http://sbi-kyc-verify.xyz/login to avoid fee.",
  "url": "http://sbi-kyc-verify.xyz/login"
}
```

**Example Response (HTTP 200 OK):**
```json
{
  "verdict": "likely scam",
  "risk_score": 94,
  "confidence": 0.94,
  "summary": "High-risk scam and phishing indicators detected across both message content and embedded URL.",
  "text_analysis": {
    "provided": true,
    "risk_score": 88,
    "probability": 0.8842,
    "detected_patterns": [
      "High urgency language ('immediately', 'urgent')",
      "Financial penalty or service disruption pressure ('locked')"
    ],
    "key_tokens": ["locked", "verify", "immediately", "fee"]
  },
  "url_analysis": {
    "provided": true,
    "risk_score": 96,
    "target_domain": "sbi-kyc-verify.xyz",
    "is_ip_address": false,
    "has_homoglyphs": false,
    "flagged_indicators": [
      "Brand name 'sbi' detected in sub-path or non-official domain",
      "Domain uses a high-risk generic top-level domain (.xyz)",
      "Insecure transport protocol (HTTP instead of HTTPS)"
    ]
  },
  "evidence": [
    "Message content: High urgency language ('immediately', 'urgent').",
    "Link security: Brand name 'sbi' detected in sub-path or non-official domain.",
    "Link security: Domain uses a high-risk generic top-level domain (.xyz)."
  ],
  "recommended_action": "Do not open the link, download attachments, or share passwords, OTPs, or financial details. If this communication claims to originate from your bank or an essential service, verify it independently using their official application or published customer service line.",
  "analyzed_at": "2026-10-20T14:30:00Z"
}
```

### 6.2 `GET /api/v1/health`
Health check and runtime status. Returns `model_loaded: true`.

### 6.3 `GET /api/v1/evaluation`
Returns the verified benchmark metrics, confusion matrix, and threshold strategy.

---

## 7. Project Architecture & File Hierarchy

```text
e:/SCAM SHIELD 01/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & static mounting
│   ├── config.py                # Typed application settings & threshold boundaries
│   ├── api/
│   │   ├── endpoints.py         # REST route handlers (/analyze, /health, /evaluation)
│   │   └── schemas.py           # Pydantic v2 request & response data contracts
│   ├── services/
│   │   ├── text_analyzer.py     # TF-IDF inference & explainability engine
│   │   ├── url_analyzer.py      # Passive zero-network lexical URL inspection
│   │   └── verdict_arbiter.py   # Multi-modal scoring policy & evidence synthesis
│   ├── models/                  # Serialized ML artifacts & evaluation metadata
│   └── static/                  # Vanilla frontend dashboard (HTML / CSS / JS)
├── data/
│   ├── processed/               # Stratified train/val/test splits (70/15/15)
│   └── synthetic/               # Seed dataset fixtures
├── docs/
│   ├── DEMO_GUIDE.md            # Live pitch presentation script & judge Q&A guide
│   └── EVALUATION_REPORT.md     # Full empirical benchmark evaluation report
├── scripts/
│   ├── prepare_data.py          # Data curation, PII scrubbing & splitting
│   ├── train.py                 # Model training & Platt probability calibration
│   └── evaluate.py              # Test set evaluation & confusion matrix generator
├── tests/
│   ├── test_sanity.py           # Environment & configuration sanity checks
│   ├── test_data_pipeline.py    # Stratification & zero-leakage verification
│   ├── test_url_analyzer.py     # Passive lexical heuristics & SSRF tests
│   ├── test_text_analyzer.py    # Classifier accuracy & explainability tests
│   ├── test_verdict_arbiter.py  # Multi-modal scoring policy & override tests
│   ├── test_api.py              # REST API integration & static asset tests
│   └── test_security.py         # SSRF immunity, XSS, payload boundary tests
├── PRD.md                       # Product Requirements Document
├── Architecture.md              # Technical Architecture & System Design
├── Rules.md                     # Operational & Engineering Rules
├── Phases.md                    # Implementation Roadmap (Phases 0–10)
├── Design.md                    # UI/UX Design System Specification
├── TASKS.md                     # Task Tracker (13/13 Completed)
├── TESTING.md                   # QA & Validation Framework
├── SECURITY.md                  # Security Policy & Threat Model (STRIDE)
├── CHANGELOG.md                 # Chronological Change Log
├── MEMORY.md                    # Project State & Verified Facts Ledger
├── requirements.txt             # Pinned Python dependencies
└── README.md                    # Project Overview (this file)
```

---

## 8. Presentation & Pitch Guide

For the competition demonstration script, timing breakdown, live scenario walk-throughs, and judge Q&A defenses, refer to [docs/DEMO_GUIDE.md](file:///e:/SCAM%20SHIELD%2001/docs/DEMO_GUIDE.md).
