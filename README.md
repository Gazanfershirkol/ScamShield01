# ScamShield AI — Multi-Modal Scam & Phishing Detection System

[![Competition](https://img.shields.io/badge/Competition-KLE_BCA_Coding_Club-0EA5E9)](#)
[![Track](https://img.shields.io/badge/Department-AI%20%2F%20ML-10B981)](#)
[![Problem Code](https://img.shields.io/badge/Problem-AI%20%C2%B7%2003-F59E0B)](#)
[![Status](https://img.shields.io/badge/Status-Planning%20%26%20Design%20Phase-6366F1)](#)

> **ScamShield AI** is an intelligent, lightweight, explainable cybersecurity tool designed to protect everyday digital users against fraudulent messages, social engineering, and deceptive phishing links. Built for the **KLE BCA Coding Club Interdepartmental Challenge**.

---

## 1. Project Overview & Problem Statement

Digital fraud delivered via SMS, WhatsApp, email, and social networks represents an escalating threat to non-technical users, students, and senior citizens. Attackers exploit psychological urgency, brand spoofing, and obscured URLs to induce credential theft and financial extortion.

**Problem Statement (AI · 03):** Design and construct a working multi-modal application that accepts message text, a URL, or both; categorizes the risk into `likely safe`, `needs review`, or `likely scam`; outputs a 0–100 risk score and plain-English evidence breakdown; exposes a documented REST API; and provides an empirical evaluation report with precision, recall, F1-score, and false-positive / false-negative error analysis.

---

## 2. Planned Features

- **Flexible Multi-Modal Analysis:** Evaluates message text alone, a URL alone, or both simultaneously.
- **Three-State Verdict Classification:** Clear, unambiguous categories:
  - `likely safe`: Low-risk benign communications.
  - `needs review`: Borderline phrasing, mixed signals, or unknown promotional domains.
  - `likely scam`: High-risk social engineering, credential theft lures, or deceptive URL structures.
- **Explainable Evidence Breakdown:** Highlights exact urgency keywords, penalty threats, brand impersonation, high-risk TLDs, and structural anomalies.
- **Interactive Web Interface:** Modern, accessible (WCAG AA compliant), cybersecurity-themed single-page dashboard featuring one-click scenario presets.
- **Documented REST API:** Interactive OpenAPI / Swagger interface for developer and judge testing (`/api/v1/analyze`, `/api/v1/health`, `/api/v1/evaluation`).
- **Zero-Network URL Inspection (SSRF Prevention):** Evaluates links strictly via offline lexical analysis; never executes network requests or DNS resolution to submitted URLs.
- **Scientific Evaluation:** Rigorous evaluation pipeline generating precision, recall, F1, confusion matrix, and qualitative error analysis.

---

## 3. Proposed Technology Stack

- **Backend:** Python 3.10+ & FastAPI (asynchronous, high-performance, Pydantic v2 validation)
- **Machine Learning Core:** scikit-learn (TF-IDF vectorizer + calibrated linear classifier)
- **URL Engine:** Pure Python lexical heuristics (`urllib.parse`, Shannon entropy, homoglyph detection)
- **Web Frontend:** Standards-compliant Vanilla HTML5, Vanilla CSS3 (custom dark tokens), Vanilla JavaScript (no node/npm build dependencies)
- **Server:** Uvicorn ASGI runner
- **Testing:** pytest & HTTPX TestClient

---

## 4. Repository Structure

```text
e:/SCAM SHIELD 01/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & static mounting
│   ├── config.py                # System settings and threshold parameters
│   ├── api/
│   │   ├── endpoints.py         # REST route handlers
│   │   └── schemas.py           # Pydantic v2 data models
│   ├── services/
│   │   ├── text_analyzer.py     # TF-IDF model inference & explainability
│   │   ├── url_analyzer.py      # Passive lexical URL inspection engine
│   │   └── verdict_arbiter.py   # Multi-modal scoring policy & evidence synthesis
│   ├── models/                  # Serialized ML artifacts & evaluation metadata
│   └── static/                  # Responsive web dashboard (HTML / CSS / JS)
├── data/
│   ├── raw/                     # Original datasets
│   └── processed/               # Anonymized, stratified train/val/test splits
├── scripts/
│   ├── prepare_data.py          # Data ingestion, scrubbing & splitting
│   ├── train.py                 # ML training & probability calibration
│   └── evaluate.py              # Test set evaluation & confusion matrix generator
├── tests/                       # Unit, integration, and security test suites
├── PRD.md                       # Product Requirements Document
├── Architecture.md              # Technical Architecture & Design Document
├── Rules.md                     # Operational & Engineering Rules
├── Phases.md                    # Sequential Implementation Roadmap
├── Design.md                    # UI/UX Design System Specification
├── TASKS.md                     # Implementation Task Tracker
├── TESTING.md                   # QA & Validation Framework
├── SECURITY.md                  # Security Policy & Threat Model
├── README.md                    # Project Overview (this file)
├── CHANGELOG.md                 # Chronological Change Log
└── MEMORY.md                    # Project State & Decision Ledger
```

---

## 5. Planned Setup & Execution Instructions

> **NOTICE:** The instructions below represent the planned execution sequence for Phase 1. Implementation is pending official Phase 0 review and approval.

```bash
# 1. Clone or navigate to the repository root
cd "e:/SCAM SHIELD 01"

# 2. Create and activate a Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies (once requirements.txt is created)
pip install -r requirements.txt

# 4. Prepare data and train baseline model
python scripts/prepare_data.py
python scripts/train.py

# 5. Run automated test suites
pytest -v

# 6. Launch the local web server
uvicorn app.main:app --reload --port 8000

# 7. Access the application:
# Web Dashboard: http://127.0.0.1:8000
# OpenAPI Docs:  http://127.0.0.1:8000/docs
```

---

## 6. Data Provenance & Ethics

- Datasets are assembled from open, publicly licensed security benchmarks (e.g., SMS Spam Collection, vetted URL abuse feeds) alongside carefully curated synthetic samples reflecting modern regional fraud patterns.
- All personal identifiable information (PII), real names, phone numbers, and specific credentials are anonymized before processing.

---

## 7. Limitations & Uncertainty Communication

- ScamShield AI provides probabilistic and heuristic risk assessments based on pattern recognition.
- It does **not** guarantee that a message is completely safe, nor does it constitute legal or cryptographic proof of fraudulent activity.
- The tool analyses URL strings lexically without live web inspection to prevent security risks (SSRF, malicious payloads); thus, compromise of legitimate domains (e.g. hacked WordPress sites) must be corroborated with message context.

---

## 8. Current Project Status

- **Current State:** Phase 0 Completed (Documentation, Architecture, Governance & Verification Strategy).
- **Application Implementation:** Pending approval to proceed with Phase 1 scaffolding.
