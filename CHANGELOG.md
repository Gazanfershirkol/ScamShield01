# Changelog — ScamShield AI

All notable changes to the ScamShield AI project will be documented chronologically in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - Phase 1: Environment Setup & Project Scaffolding (2026-10-20)

### Added
- Configured Python 3.11.9 virtual environment (`.venv`) and pinned 43 dependencies in `requirements.txt`.
- Initialized Git repository in `e:/SCAM SHIELD 01/` via `git init` (branch `main`).
- Created `.gitignore` excluding `.venv/`, `__pycache__/`, `.pytest_cache/`, `.env`, model binaries (`*.joblib`, `*.pkl`), raw and processed datasets, and IDE/OS noise.

### Changed
- Aligned mock evaluation `scam_threshold` from `0.70` to `0.75` in `Architecture.md` to match arbiter and configuration constants.
- Updated `TASKS.md`: T-001 marked **DONE**, T-002 marked **DONE**, T-003 marked **IN_PROGRESS**.
- Updated `MEMORY.md`: Removed Python blocker, verified Python 3.11.9 runtime and library availability.

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
