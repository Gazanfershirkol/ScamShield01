# Engineering Rules & Operational Constraints — ScamShield AI

These rules are strictly binding on all contributors, coding agents, and automated tools working on the **ScamShield AI** codebase. Every code modification, commit, and pull request must adhere to these directives.

---

## 1. Codebase Integrity & Discipline

1. **Inspect Before Editing:** Always inspect existing files, dependencies, and configuration before authoring or modifying code. Never assume a file is empty or non-existent without verification.
2. **Phase Boundary Enforcement:** Execute work strictly within the scope of the currently authorized implementation phase (as defined in `Phases.md`). Do not jump ahead to future phases without explicit approval.
3. **No Fabrication of Results:** Never fabricate or falsify implementation status, unit test results, training logs, accuracy numbers, F1 scores, or research citations. If an experiment has not been run or a test is pending, explicitly label it as `UNVERIFIED` or `PENDING`.
4. **No Degradation to Stubs:** Never replace functional code, comprehensive implementations, or verified tests with dummy stubs, placeholders, or empty `pass` statements.
5. **YAGNI (You Aren't Gonna Need It):** Avoid unnecessary abstractions, premature design patterns, complex meta-programming, or bloated utility wrappers. Write clear, direct, and purposeful code.
6. **Code Style & Readability:**
   - Adhere to Python PEP 8 standards.
   - Use strict type annotations (`typing.Optional`, `typing.List`, `typing.Dict`, `typing.Tuple`).
   - Use descriptive, intention-revealing variable and function names.
   - Keep functions focused and modular (< 50 lines per function where feasible).
   - Write clear docstrings explaining arguments, return values, and edge conditions.
7. **Change Preservation:** Do not delete files, overwrite important training datasets, install major dependencies, or perform destructive Git operations (`git reset --hard`, `git push --force`) without concrete justification and approval.

---

## 2. Security & Untrusted Input Handling

1. **Zero-Fetch URL Policy (SSRF Immunity):** Under no circumstance may any backend service, script, or utility execute an HTTP request, TCP socket connection, or DNS resolution towards a user-submitted URL during analysis. All URL evaluations must remain **100% passive, offline, and lexical**.
2. **Treat All External Data as Hostile:** All user inputs (message text, URLs, query parameters, API request bodies) are untrusted. Enforce strict character limits (Text: max 10,000 chars; URL: max 2,048 chars) and reject malformed encodings immediately.
3. **No Dynamic Execution of Untrusted Content:** Never pass user-submitted strings to `eval()`, `exec()`, `os.system()`, or shell subprocesses.
4. **XSS & Injection Prevention:**
   - In the frontend, render all dynamic user content and analysis results strictly using safe DOM manipulation (`element.textContent` or sanitized template interpolation). Never use `innerHTML` on raw or unescaped strings.
   - In the backend, sanitize file paths and prevent path traversal (`os.path.abspath`, verifying paths stay within designated directories).
5. **Safe Logging & PII Minimization:** Never log unmasked user messages, passwords, API tokens, or phone numbers. Truncate and mask input strings in application logs.
6. **Secret Management:** Never commit secrets, private keys, access tokens, or sensitive credentials to Git. Use environment variables and `.env.example` templates.

---

## 3. Machine Learning & Scientific Rigor

1. **Statistical Honesty & Probability Calibration:** Never describe an output score as a "calibrated probability" unless formal calibration (such as Platt scaling / `CalibratedClassifierCV` or isotonic regression on a held-out validation set) has been empirically performed and verified via calibration curves / Brier score. Otherwise, term it a "heuristic risk score" or "decision confidence index".
2. **Leakage Prevention:**
   - Strictly separate the dataset into Train, Validation, and Test splits *before* fitting any feature extractors.
   - Fit vectorizers (e.g., `TfidfVectorizer`) **only** on the training set. Never fit or peek on validation or test sets.
3. **Deterministic Reproducibility:** Always set explicit random seeds (`random_state=42`) across all data splitting, model training, and evaluation scripts to ensure 100% reproducible outcomes.
4. **Metric Transparency:** Always report Precision, Recall, and F1-score concurrently. Never report Accuracy in isolation, particularly on imbalanced fraud datasets.
5. **Clear Uncertainty Communication:** The system must visibly convey model uncertainty. Never output statements asserting that a message is "100% guaranteed safe" or "conclusive legal proof of fraud".

---

## 4. Testing & Verification Requirements

1. **Continuous Verification:** Execute targeted unit and integration tests after every functional change before marking any task as complete.
2. **Regression Testing:** Ensure that changes to heuristic scoring rules or model feature weights do not break baseline test cases for benign messages or known phishing patterns.
3. **Architectural Deviation Tracking:** Any necessary architectural deviation from `Architecture.md` must be formally recorded in `CHANGELOG.md` and `MEMORY.md` before implementation.
