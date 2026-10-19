# Changelog — ScamShield AI

All notable changes to the ScamShield AI project will be documented chronologically in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - Phase 1: Repository Baseline (2026-10-19)

### Added
- Initialized Git repository in `e:/SCAM SHIELD 01/` via `git init` (branch `main`).
- Created `.gitignore` excluding `.venv/`, `__pycache__/`, `.pytest_cache/`, `.env`, model binaries (`*.joblib`, `*.pkl`), raw and processed datasets, and IDE/OS noise. Approved Markdown documentation files are explicitly not excluded.

### Changed
- Staged and committed 12 files (11 Markdown specs + `.gitignore`) as root commit `8c214e9` with message: `chore(phase-0): add project governance documentation baseline`.
- Updated `TASKS.md`: T-001 marked **DONE**; T-002 marked **BLOCKED**.
- Updated `MEMORY.md`: Phase 1 command log appended with verified real outputs; blockers updated.

### Blocked
- T-002 (Python virtual environment setup) is blocked: `python --version`, `py --version`, and `py -0p` all confirm no Python interpreter is registered on the host PATH.

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
