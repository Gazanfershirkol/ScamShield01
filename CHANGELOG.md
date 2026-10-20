# Changelog — ScamShield AI

All notable changes to the ScamShield AI project will be documented chronologically in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
