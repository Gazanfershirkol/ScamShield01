# Changelog — ScamShield AI

All notable changes to the ScamShield AI project will be documented chronologically in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - Phase 6: FastAPI Application & REST Endpoints (2026-10-20)

### Added
- Implemented `app/api/schemas.py` defining Pydantic v2 data models for `AnalyzeRequest` (with input length boundaries and whitespace checks), `AnalyzeResponse`, `HealthResponse`, and `EvaluationResponse`.
- Implemented `app/api/endpoints.py` providing `POST /api/v1/analyze`, `GET /api/v1/health`, and `GET /api/v1/evaluation`.
- Implemented `app/main.py` configuring FastAPI bootstrap, CORS middleware, API v1 routing, and static file asset serving.
- Created `tests/test_api.py` with 10 integration tests (100% pass) verifying health checks, dual modality analysis, single-mode analysis, 422 validation on empty/whitespace/oversized inputs, evaluation metrics, and OpenAPI `/docs`.

### Changed
- Updated `TASKS.md`: Task T-008 marked **DONE** (9/13 total tasks completed).
- Updated `MEMORY.md`: Recorded Phase 6 completion and transitioned active goal to Phase 7.

---

## [Unreleased] - Phase 5: Verdict Arbiter & Evidence Synthesis Engine (2026-10-20)

### Added
- Implemented `app/services/verdict_arbiter.py` providing multi-modal score blending, signal harmonization, and evidence synthesis.
- Implemented composite scoring formula: `max(0.55 * Text + 0.45 * URL, 0.85 * max(Text, URL))` with single-modality fallback.
- Added safety overrides: raw IP hostname with credential lures automatically escalates to `likely scam`, and cross-modal signal divergence (`|Text - URL| > 50`) automatically escalates to at least `needs review`.
- Implemented accessible plain-English evidence synthesis bullet points, context-aware 1-sentence summaries, and protective action recommendations.
- Created `tests/test_verdict_arbiter.py` with 11 automated unit tests (100% pass) verifying high-risk alignment, safe baseline, conflicting signals, critical IP override, divergence escalation, and dictionary serialization.

### Changed
- Updated `TASKS.md`: Task T-007 marked **DONE** (8/13 total tasks completed).
- Updated `MEMORY.md`: Recorded Phase 5 completion, updated commands ledger, and transitioned active goal to Phase 6.

---

## [Unreleased] - Phase 4: Text Classification Engine (2026-10-20)

### Added
- Implemented `scripts/train.py`: fits `TfidfVectorizer` (1-2 n-grams, 5000 max features), trains `LogisticRegression(class_weight='balanced')`, calibrates probabilities with Platt scaling (`CalibratedClassifierCV`), and serializes model bundle to `app/models/text_model.joblib`.
- Implemented `app/services/text_analyzer.py` with singleton model loader, microsecond probability inference, dot-product token explainability, and semantic pattern tag generation.
- Created `tests/test_text_analyzer.py` with 8 unit tests (100% pass) verifying urgency detection, benign messages, explainability token extraction, and 10,000 character payload limits.

### Changed
- Updated `TASKS.md`: T-006 marked **DONE** (7/13 total tasks completed).
- Updated `MEMORY.md`: Recorded Phase 4 completion and model metrics.

---

## [Unreleased] - Phase 3: URL Passive Lexical Analysis Engine (2026-10-20)

### Added
- Implemented `app/services/url_analyzer.py` providing 100% passive, offline lexical and structural URL evaluation.
- Added 10 explicit heuristic indicators: IP address host (+45), `@` credential deception (+35), brand in subdomain (+35), punycode/homoglyphs (+30), high-risk TLDs (+20), suspicious path keywords (+15), high domain Shannon entropy (+15), insecure HTTP (+20), and trusted canonical domain safeguards (-30).
- Created `tests/test_url_analyzer.py` with 10 unit and security tests (100% pass in 0.16s), including a monkeypatch socket/HTTP test guaranteeing zero network calls (SSRF immunity).

### Changed
- Updated `TASKS.md`: T-005 marked **DONE** (6/13 total tasks completed).
- Updated `MEMORY.md`: Recorded Phase 3 completion and verified test outputs.

---

## [Unreleased] - Phase 2: Data Curation & Dataset Pipeline (2026-10-20)

### Added
- Created data curation, PII scrubbing, and stratified splitting pipeline in `scripts/prepare_data.py`.
- Generated 2,500 unique post-scrubbed benchmark messages (1,500 benign, 1,000 scam).
- Created 70/15/15 stratified train/val/test splits (1,750 / 375 / 375 rows) with deterministic `random_state=42`.
- Created automated pipeline test suite in `tests/test_data_pipeline.py` (6 tests, 100% pass) verifying split sizes, binary labels, 40.0% class ratio, and zero cross-split leakage.

### Changed
- Updated `TASKS.md`: T-004 marked **DONE** (5/13 total tasks completed).
- Updated `MEMORY.md`: Recorded Phase 2 completion and verified test outputs.

---

## [Unreleased] - Phase 1: Environment Setup & Project Scaffolding (2026-10-20)

### Added
- Configured Python 3.11.9 virtual environment (`.venv`) and pinned 43 dependencies in `requirements.txt`.
- Initialized Git repository in `e:/SCAM SHIELD 01/` via `git init` (branch `main`).
- Created `.gitignore` excluding `.venv/`, `__pycache__/`, `.pytest_cache/`, `.env`, model binaries, raw/processed datasets, and IDE/OS noise.
- Scaffolded project directories: `app/`, `data/`, `scripts/`, `tests/`.
- Created `app/config.py` with immutable typed `Settings` class and default thresholds.
- Created `tests/test_sanity.py` with 4 environment and configuration tests (100% pass).

### Changed
- Aligned mock evaluation `scam_threshold` from `0.70` to `0.75` in `Architecture.md` to match arbiter and configuration constants.
- Updated `TASKS.md`: T-001, T-002, and T-003 marked **DONE**.
- Updated `MEMORY.md`: Removed Python blocker, verified Python 3.11.9 runtime.

---

## [Unreleased] - Phase 0: Project Initiation & Architecture Planning (2026-10-19)

### Added
- Completed initial workspace and environment inspection.
- Identified empty workspace root (`e:/SCAM SHIELD 01`).
- Detected Git availability (`C:\Program Files\Git\cmd\git.exe`).
- Discovered absence of recognized Python binary in standard system PATH.
- Created complete project governance and engineering specifications:
  - `PRD.md`: Product Requirements Document detailing problem statement, user journeys, functional and non-functional requirements, and acceptance criteria.
  - `Architecture.md`: Technical design, component diagrams, API schemas, data flow, ML pipeline, URL analysis heuristics, and directory structure.
  - `Rules.md`: Strict operational and development directives for zero-fetch URL policy, no data fabrication, type hints, and deterministic reproducibility.
  - `Phases.md`: Ten sequential implementation phases with prerequisites, verification commands, and rollback procedures.
  - `Design.md`: UI/UX design specifications, CSS custom tokens, accessibility standards, responsive layouts, and state handling.
  - `TASKS.md`: Granular task inventory tracking priorities, dependencies, and execution states.
  - `TESTING.md`: QA strategy covering unit/integration testing, data leakage prevention, class imbalance, confusion matrix, and error analysis.
  - `SECURITY.md`: Comprehensive threat modeling (STRIDE), SSRF prevention via zero-fetch architecture, XSS mitigation, and safe logging.
  - `README.md`: Project summary, planned architecture, setup guide, and responsible use disclaimers.
  - `CHANGELOG.md`: Chronological log of actual repository events.
  - `MEMORY.md`: Engineering memory ledger capturing verified facts, decisions, and exact next steps.
