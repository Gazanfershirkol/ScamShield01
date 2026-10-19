# Project State & Memory Ledger — ScamShield AI

**Last Updated:** 2026-10-19T15:45:00+05:30  
**Current Phase:** Phase 1 (Environment Setup & Project Scaffolding) — **IN PROGRESS** (partially complete; blocked on Python)  
**Next Phase:** Phase 1 Task T-002 — **BLOCKED** (Python interpreter required)

---

## 1. Verified Facts (Empirically Confirmed)

1. **Workspace Root:** `e:/SCAM SHIELD 01` was initially completely empty. No existing files, source code, git repository, virtual environments, or datasets existed prior to Phase 0.
2. **Version Control:** Git binary is available on the host at `C:\Program Files\Git\cmd\git.exe`, but `.git` repository has not yet been initialized in `e:/SCAM SHIELD 01`.
3. **Python Runtime Status:** 
   - `python` command is not currently mapped in standard PowerShell PATH.
   - `py.exe` launcher exists at `C:\Windows\py.exe`, but `py -0p` and `py -V` report: `"No installed Python found!"` in the current terminal environment.
   - No Python installations were detected in standard directories (`C:\Program Files\Python*`, `C:\Users\GAZANFER SHIRKOL\AppData\Local\Programs\Python*`).
4. **Operating Environment:** Windows 11 host operating system. Local shell is PowerShell.
5. **Competition Deadline:** 22 October 2026 (~3 days remaining).
6. **Documentation Deliverables:** All 11 foundational Markdown documents have been authored in the project root: `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`, `TASKS.md`, `TESTING.md`, `SECURITY.md`, `README.md`, `CHANGELOG.md`, `MEMORY.md`.

---

## 2. Approved Architectural & Engineering Decisions

1. **Tech Stack Selection:**
   - Backend: Python with **FastAPI** (fast, typed, automatic OpenAPI documentation).
   - Core ML: **scikit-learn** using `TfidfVectorizer` (n-grams 1-2) with calibrated `LogisticRegression` (fast inference, microsecond cold start, high interpretability via feature coefficients).
   - URL Engine: Pure Python lexical/heuristic analyzer (`urllib.parse`, Shannon entropy, homoglyph check) with **100% offline zero-network fetch policy**.
   - Frontend: **Vanilla HTML5, CSS3, and JavaScript** (no node/npm build step, no Tailwind bloat, maximum portability and resilience).
   - Server: Uvicorn on `http://127.0.0.1:8000`.
2. **Persistence Policy:** Ephemeral in-memory analysis. Zero database required. Zero user data retention.
3. **Security Policy:** Submitted URLs are never resolved or fetched over HTTP/TCP/DNS. Inputs capped at 10,000 characters for text and 2,048 characters for URLs.
4. **Verdict Policy:** Three-state standardized output (`likely safe`, `needs review`, `likely scam`) paired with normalized 0–100 risk score and plain-English explanatory evidence breakdown.
5. **Evaluation Protocol:** 70/15/15 stratified train/val/test split. TF-IDF vectorizer fit strictly on train split. Held-out test set sealed until final evaluation script run.

---

## 3. Assumptions (Requiring Verification Before/During Phase 1)

1. The project owner or system administrator will either point to an existing Python installation or install Python 3.10+ (via Microsoft Store, winget, or official python.org installer) before Phase 1 dependencies can be installed.
2. A balanced open-source dataset (e.g. SMS Spam Collection benchmark) can be ingested locally or augmented with synthetic regional scam templates without network dependency during execution.

---

## 4. Commands Actually Executed & Real Observed Results

| Timestamp (UTC) | Command Executed | Exit Code | Observed Output / Effect |
| :--- | :--- | :--- | :--- |
| 2026-10-19 09:25 | `list_dir(e:/SCAM SHIELD 01)` | 0 | Directory confirmed empty. |
| 2026-10-19 09:43 | `Get-ChildItem -Force; git status` | 1 | No files found; "fatal: not a git repository". |
| 2026-10-19 09:43 | `python --version` | 1 | "python : The term 'python' is not recognized..." |
| 2026-10-19 09:44 | `Get-Command py, python, python3` | 0 | `py.exe` located at `C:\Windows\py.exe`. |
| 2026-10-19 09:45 | `py -0p` | 0 | "No installed Pythons found!" |
| 2026-10-19 09:46 | Common Python path search | 0 | No Python directories located in standard paths. |
| 2026-10-19 09:47 | `where.exe git` | 0 | `git.exe` at `C:\Program Files\Git\cmd\git.exe`. |
| 2026-10-19 09:48 | `where.exe python` | 1 | "INFO: Could not find files..." |
| 2026-10-19 09:56 | `py -V` | 1 | "No installed Python found!" |
| 2026-10-19 10:02 | File authoring: 11 markdown specs | 0 | All documents written to `e:/SCAM SHIELD 01/`. |
| 2026-10-19 10:07 | `git config --global user.name/email` | 0 | Identity: `Gazan` / `gazanfer2006@gmail.com`. |
| 2026-10-19 10:08 | `git -C "e:\SCAM SHIELD 01" init` | 0 | "Initialized empty Git repository in E:/SCAM SHIELD 01/.git/" |
| 2026-10-19 10:09 | Created `.gitignore` (65-line spec) | 0 | File written to `e:/SCAM SHIELD 01/.gitignore`. |
| 2026-10-19 10:09 | `git status --short` (pre-stage) | 0 | 12 untracked files listed: 11 Markdown docs + `.gitignore`. No secrets or unexpected files. |
| 2026-10-19 10:10 | `git add` (12 files, named explicitly) | 0 | All 12 staged; LF→CRLF warnings are normal on Windows; no errors. |
| 2026-10-19 10:10 | `git diff --cached --stat` | 0 | 12 files, 1617 insertions; verified staged set matches intended list. |
| 2026-10-19 10:10 | `git commit` (Phase 0 baseline) | 0 | Commit `8c214e9` on branch `main`. Message: "chore(phase-0): add project governance documentation baseline". |
| 2026-10-19 10:11 | `git log --oneline -3` | 0 | Shows single commit `8c214e9` — clean root commit. |
| 2026-10-19 10:11 | `git status --short` (post-commit) | 0 | Empty — working tree clean. |
| 2026-10-19 10:12 | `python --version` | 1 | "python : The term 'python' is not recognized..." |
| 2026-10-19 10:13 | `py --version` | 112 | "No installed Python found!" (exit code 112) |
| 2026-10-19 10:14 | `py -0p` | 0 | "No installed Pythons found!" |

---

## 5. Implemented Features

- **Completed (Phase 0):** All 11 governance Markdown documents authored and verified.
- **Completed (Phase 1, partial):** Git repository initialized; `.gitignore` created; Phase 0 documentation baseline committed to `main` as commit `8c214e9`.
- **Pending (Phase 1):** Python virtual environment creation and dependency installation (T-002) — BLOCKED.

---

## 6. Known Blockers

- **Host Python Environment (ACTIVE BLOCKER for T-002, T-003, and all subsequent tasks):** A functioning Python 3.10+ interpreter must be available on the Windows system PATH before creating a virtual environment or running any scripts.
  - `python --version` → not recognized in PATH.
  - `py --version` → `No installed Python found!` (exit code 112).
  - `py -0p` → `No installed Pythons found!`
  - **Action required:** Install Python 3.10+ and verify it appears in PATH before proceeding.

---

## 7. Open Questions

1. Does the project owner have Python 3.10+ installed in a non-standard location (e.g. Anaconda, Miniconda, WSL, or a custom drive), or will they install it via one of the recommended methods below?

   **Recommended installation options (in order of ease on Windows):**
   - **Microsoft Store:** Search "Python 3.12" — installs to `%LOCALAPPDATA%\Programs\Python` and auto-registers with the `py` launcher.
   - **winget (if available):** `winget install -e --id Python.Python.3.12`
   - **Official installer:** Download from https://www.python.org/downloads/ — check ✅ "Add Python to PATH" during setup.

   Once Python is installed, run `py -V` or `python --version` to confirm, then report the exact version string.

---

## 8. Exact Next Action

**Prerequisite (user action required):** Install Python 3.10+ and confirm it is available in PATH.

**Then — Task T-002 (Phase 1):** Create Python virtual environment (`.venv`) and author `requirements.txt` with pinned minimal dependencies.
