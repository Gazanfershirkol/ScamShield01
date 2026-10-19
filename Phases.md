# Implementation Roadmap & Sequential Phases — ScamShield AI

This document establishes the precise, sequential execution roadmap for developing ScamShield AI. Each phase is self-contained with explicit dependencies, verification commands, observable completion criteria, failure modes, and rollback strategies.

---

## Phase 0: Workspace Inspection & Architecture Planning (Current Phase)
- **Objective:** Inspect existing workspace, verify tools/environment, establish comprehensive architectural and engineering governance, and create unified project Markdown specifications.
- **Files Affected:** `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`, `TASKS.md`, `TESTING.md`, `SECURITY.md`, `README.md`, `CHANGELOG.md`, `MEMORY.md`.
- **Dependencies:** None.
- **Implementation Tasks:**
  1. Inspect root filesystem, check Git repository status, locate Python and development tools.
  2. Synthesize comprehensive system specification documents.
  3. Perform cross-document consistency audit.
- **Tests & Verification:**
  - `Get-ChildItem -Force`
  - Cross-document link and term verification.
- **Observable Completion Criteria:** All 11 Markdown documents created in project root with zero contradictions and strict adherence to competition constraints.
- **Likely Failure Modes:** Scope creep, premature coding before documentation approval.
- **Rollback Approach:** Git is not yet initialized; documentation can be edited or restored directly.

---

## Phase 1: Environment & Project Scaffolding
- **Objective:** Initialize Git version control, configure Python virtual environment, install pinned dependencies, create the core directory tree, and verify the basic sanity test suite.
- **Files Affected:** `.gitignore`, `requirements.txt`, `app/__init__.py`, `app/config.py`, `tests/__init__.py`, `tests/test_sanity.py`.
- **Dependencies:** Approval of Phase 0 documentation; availability of a working Python 3.10+ installation.
- **Implementation Tasks:**
  1. Initialize Git repository (`git init`) and commit documentation baseline.
  2. Create Python virtual environment (`.venv`).
  3. Author `requirements.txt` with pinned dependencies (`fastapi`, `uvicorn`, `scikit-learn`, `pydantic`, `pytest`, `joblib`).
  4. Create complete directory hierarchy as defined in `Architecture.md`.
  5. Author `app/config.py` with typed configuration settings.
  6. Author `tests/test_sanity.py` to verify pytest and environment health.
- **Tests & Verification:**
  - `pytest tests/test_sanity.py`
  - `git status`
- **Observable Completion Criteria:** `pytest` passes with 100% green; `app/config.py` is importable without errors.
- **Likely Failure Modes:** Missing Python binary on host machine; wheel build errors on Windows.
- **Rollback Approach:** Delete `.venv`, reinstall dependencies with precompiled wheels.

---

## Phase 2: Data Curation & Dataset Pipeline
- **Objective:** Curate synthetic and open-source benchmark training/validation/test datasets for scam text and phishing URLs, enforce anonymization, and create reproducible train/val/test splits.
- **Files Affected:** `data/raw/`, `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv`, `scripts/prepare_data.py`, `tests/test_data_pipeline.py`.
- **Dependencies:** Phase 1 complete.
- **Implementation Tasks:**
  1. Assemble balanced SMS/messaging scam dataset and benign messages (curated from open benchmarks and synthetic realistic regional samples).
  2. Implement `scripts/prepare_data.py`:
     - Deduplication and text normalization.
     - PII scrub (phone numbers, real names, personal emails replaced with tokens).
     - Stratified split: 70% Train, 15% Validation, 15% Held-out Test (`random_state=42`).
  3. Verify class distribution balance and absence of test set leakage.
- **Tests & Verification:**
  - `python scripts/prepare_data.py`
  - `pytest tests/test_data_pipeline.py`
- **Observable Completion Criteria:** Clean CSV splits created in `data/processed/`; zero overlap between Train, Val, and Test sets; test passes.
- **Likely Failure Modes:** Label imbalance; text encoding/Unicode errors.
- **Rollback Approach:** Re-run `prepare_data.py` with fixed encoding parameters (`utf-8`).

---

## Phase 3: URL Passive Lexical Analysis Engine
- **Objective:** Build and test the zero-network passive URL analyzer to extract structural and lexical risk indicators.
- **Files Affected:** `app/services/url_analyzer.py`, `tests/test_url_analyzer.py`.
- **Dependencies:** Phase 1 complete.
- **Implementation Tasks:**
  1. Implement `analyze_url(url: str) -> URLAnalysisResult` in `app/services/url_analyzer.py`:
     - Parse components with `urllib.parse`.
     - Check IPv4/IPv6 hostname patterns.
     - Detect homoglyphs / punycode prefixes (`xn--`).
     - Calculate Shannon entropy for domain labels.
     - Match against high-risk TLDs and brand-impersonation keyword lists.
     - Detect embedded credentials (`@`), excessive subdomains, and suspicious path tokens (`login`, `verify`, `kyc`).
  2. Implement unit tests covering known phishing URL structures, benign top domains, malformed strings, and edge cases.
- **Tests & Verification:**
  - `pytest tests/test_url_analyzer.py`
- **Observable Completion Criteria:** Analyzer passes all unit tests, executes in < 2ms per URL, and never opens network connections.
- **Likely Failure Modes:** ReDoS in regex patterns; incorrect parsing of scheme-less URLs.
- **Rollback Approach:** Revert regex modifications and rely on strict `urllib.parse` tokenization.

---

## Phase 4: Text Classification Engine
- **Objective:** Train, calibrate, evaluate, and serialize the scikit-learn TF-IDF linear classification model for message fraud detection.
- **Files Affected:** `scripts/train.py`, `app/services/text_analyzer.py`, `app/models/text_model.joblib`, `tests/test_text_analyzer.py`.
- **Dependencies:** Phase 2 (clean data splits) and Phase 1.
- **Implementation Tasks:**
  1. Implement `scripts/train.py`:
     - Fit `TfidfVectorizer(ngram_range=(1,2), max_features=5000)` strictly on `train.csv`.
     - Train `LogisticRegression(class_weight='balanced', random_state=42)`.
     - Calibrate probabilities using validation split (`CalibratedClassifierCV`).
     - Export serialized model pipeline to `app/models/text_model.joblib`.
  2. Implement `app/services/text_analyzer.py` to load artifact, run inference, and extract top positive/negative token indicators.
  3. Author unit tests for clean inference, empty text handling, and explainability extraction.
- **Tests & Verification:**
  - `python scripts/train.py`
  - `pytest tests/test_text_analyzer.py`
- **Observable Completion Criteria:** Model serialized to disk; inference produces calibrated probability and explainable token lists; test suite passes.
- **Likely Failure Modes:** Feature vocabulary mismatch; serialization version incompatibility.
- **Rollback Approach:** Re-train and re-serialize using matching package versions.

---

## Phase 5: Verdict & Evidence Synthesis Engine
- **Objective:** Integrate text analysis and URL analysis into a unified decision arbiter that generates verdicts, normalized risk scores, and human-readable evidence points.
- **Files Affected:** `app/services/verdict_arbiter.py`, `tests/test_verdict_arbiter.py`.
- **Dependencies:** Phase 3 (URL Engine) and Phase 4 (Text Engine).
- **Implementation Tasks:**
  1. Implement scoring policy in `app/services/verdict_arbiter.py`:
     - Dual-mode blending formula: `Overall Score = max(Text_Score * 0.55 + URL_Score * 0.45, max(Text_Score, URL_Score) * 0.85)`.
     - Single-mode fallback (text only or URL only).
     - Explicit verdict thresholds (`likely safe` < 35, `needs review` 35–74, `likely scam` ≥ 75).
     - Override rules for severe red flags (e.g. IP hostname + credential lure).
  2. Synthesize plain-English evidence list and recommended protective action.
  3. Author comprehensive unit tests covering all permutations (both inputs, text only, URL only, conflicting signals).
- **Tests & Verification:**
  - `pytest tests/test_verdict_arbiter.py`
- **Observable Completion Criteria:** Deterministic verdict generation across all test cases with informative, accessible explanations.
- **Likely Failure Modes:** Ambiguous verdict boundaries; contradictory explanations.
- **Rollback Approach:** Adjust weight coefficients and threshold constants in `app/config.py`.

---

## Phase 6: FastAPI Application & REST Endpoints
- **Objective:** Expose the analysis pipeline via robust, documented REST API endpoints with Pydantic validation and error handling.
- **Files Affected:** `app/main.py`, `app/api/endpoints.py`, `app/api/schemas.py`, `tests/test_api.py`.
- **Dependencies:** Phase 5 complete.
- **Implementation Tasks:**
  1. Create Pydantic v2 schemas for request and response models in `app/api/schemas.py`.
  2. Implement endpoints in `app/api/endpoints.py`:
     - `POST /api/v1/analyze`: Core analysis pipeline.
     - `GET /api/v1/health`: Liveness & model status.
     - `GET /api/v1/evaluation`: Static benchmark metrics summary.
  3. Mount routers in `app/main.py`, configure CORS for local testing, and set up custom exception handlers.
  4. Write integration tests with `httpx` / `TestClient`.
- **Tests & Verification:**
  - `pytest tests/test_api.py`
- **Observable Completion Criteria:** All endpoints return valid JSON; input validation correctly rejects invalid payloads; OpenAPI docs accessible at `/docs`.
- **Likely Failure Modes:** Schema validation errors on edge cases; async execution deadlocks.
- **Rollback Approach:** Use synchronous route handlers where heavy async logic is unneeded.

---

## Phase 7: Web User Interface (Single-Page Dashboard)
- **Objective:** Construct a high-performance, responsive, accessible Vanilla HTML/CSS/JS web dashboard connected to the backend API.
- **Files Affected:** `app/static/index.html`, `app/static/css/style.css`, `app/static/js/app.js`, `app/main.py`.
- **Dependencies:** Phase 6 complete.
- **Implementation Tasks:**
  1. Author `index.html` with semantic structure, accessible landmarks, and WCAG AA compliance.
  2. Implement `style.css` using sleek cybersecurity dark palette, responsive CSS Grid/Flexbox, distinct verdict badges, and crisp typography.
  3. Implement `app.js`:
     - Asynchronous fetch calls to `/api/v1/analyze`.
     - Dynamic rendering of verdict, score gauge/bar, evidence bullets, and recommended action.
     - Interactive scenario presets ("Bank Phishing", "Job Scam", "Clean Invoice", "Suspicious Shortlink").
     - Keyboard navigation (Ctrl+Enter to submit) and accessible focus management.
  4. Mount static directory in `app/main.py`.
- **Tests & Verification:**
  - Start local server (`uvicorn app.main:app --port 8000`) and verify UI manually across mobile and desktop viewports.
- **Observable Completion Criteria:** Web UI renders seamlessly at `http://127.0.0.1:8000/`; interactive presets trigger instant analysis; error states handle server outages gracefully.
- **Likely Failure Modes:** Broken static file mounting; CSS layout overflow on mobile screens.
- **Rollback Approach:** Use standard relative asset paths and strict viewport meta tags.

---

## Phase 8: Model Evaluation & Benchmark Reporting
- **Objective:** Execute formal benchmark evaluation on the held-out test split, compute metrics, generate the confusion matrix, perform error analysis, and export the official report.
- **Files Affected:** `scripts/evaluate.py`, `app/models/evaluation_meta.json`, `docs/EVALUATION_REPORT.md`.
- **Dependencies:** Phase 2, Phase 4, and Phase 5.
- **Implementation Tasks:**
  1. Implement `scripts/evaluate.py`:
     - Evaluate model on `data/processed/test.csv`.
     - Calculate Precision, Recall, F1 (macro and per-class), and ROC-AUC.
     - Generate Confusion Matrix.
     - Conduct qualitative analysis of False Positives and False Negatives.
  2. Save metrics summary to `app/models/evaluation_meta.json` for consumption by `/api/v1/evaluation`.
  3. Author `docs/EVALUATION_REPORT.md` documenting scientific methodology and results.
- **Tests & Verification:**
  - `python scripts/evaluate.py`
  - `pytest tests/test_api.py -k test_evaluation_endpoint`
- **Observable Completion Criteria:** Detailed evaluation report generated; metrics successfully populated in API endpoint.
- **Likely Failure Modes:** Degraded recall on subtle scam phrasing; division by zero on zero-support classes.
- **Rollback Approach:** Ensure stratified sampling and balanced class weights.

---

## Phase 9: Security Hardening & Edge-Case Verification
- **Objective:** Verify system boundaries against malicious inputs, SSRF, XSS payloads, ReDoS, and oversized buffers.
- **Files Affected:** `tests/test_security.py`, `SECURITY.md`.
- **Dependencies:** Phases 1–7 complete.
- **Implementation Tasks:**
  1. Author `tests/test_security.py`:
     - Test input strings containing `<script>`, `javascript:`, SQL injection, and null bytes.
     - Test 100,000-character payload rejection.
     - Verify zero network traffic when analyzing exotic URL schemes (`file://`, `gopher://`, `localhost`).
  2. Implement any necessary input clamping or sanitize filters.
- **Tests & Verification:**
  - `pytest tests/test_security.py`
- **Observable Completion Criteria:** All security tests pass with 0 leaks or crashes.
- **Likely Failure Modes:** Regex catastrophic backtracking on long crafted URLs.
- **Rollback Approach:** Set timeout and length limits on regex executions.

---

## Phase 10: Final Documentation, Verification & Submission Package
- **Objective:** Finalize all documentation, verify end-to-end setup instructions, prepare presentation demo notes, and package the repository for competition submission.
- **Files Affected:** `README.md`, `CHANGELOG.md`, `MEMORY.md`, `docs/DEMO_GUIDE.md`.
- **Dependencies:** All previous phases complete.
- **Implementation Tasks:**
  1. Verify setup instructions from a clean state.
  2. Record final state in `MEMORY.md` and `CHANGELOG.md`.
  3. Create presentation demo script and key talking points for the two-person team.
- **Tests & Verification:**
  - Run full test suite: `pytest`
- **Observable Completion Criteria:** 100% tests passing; clean Git repository ready for hackathon evaluation.
- **Likely Failure Modes:** Outdated documentation not matching final code.
- **Rollback Approach:** Conduct thorough documentation audit against implemented codebase.
