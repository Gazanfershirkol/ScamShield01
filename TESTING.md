# Testing Strategy & Quality Assurance Framework — ScamShield AI

This document establishes the scientific validation, quality assurance, and automated testing protocols for ScamShield AI. It enforces strict separation between targets and measured results, prevents data leakage, and provides actionable guidelines for investigating model failure modes.

---

## 1. Testing Hierarchy & Scope

```text
+-------------------------------------------------------+
|                 End-to-End & UI Verification          |
|      (Interactive presets, browser responsiveness)    |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|                 API & Integration Tests               |
|    (FastAPI TestClient, schemas, error status codes)  |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|               Subsystem & Unit Tests                  |
|    (Text TF-IDF classifier, URL heuristics, Arbiter)  |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|         Data Pipeline & Integrity Verifications       |
|    (Leakage checks, stratified split validation)      |
+-------------------------------------------------------+
```

---

## 2. Dataset Partitioning & Leakage Prevention

### 2.1 Split Methodology
- **Total Dataset:** Curated benchmark comprising legitimate and fraudulent communications.
- **Ratios:**
  - **Train Set (70%):** Exclusively utilized to fit the `TfidfVectorizer` vocabulary and train model weights.
  - **Validation Set (15%):** Utilized for hyperparameter tuning, probability calibration (`CalibratedClassifierCV`), and decision threshold selection.
  - **Held-out Test Set (15%):** Sealed during training. Evaluated exactly once at final benchmark time to produce competition metrics.
- **Stratification:** Splitting is stratified on the target class (`label`: 0 for safe/benign, 1 for scam/phishing) to preserve the exact class ratio across all splits.
- **Deterministic Seed:** All splits must use `random_state=42`.

### 2.2 Leakage Prevention Rules
1. **Vocabulary Isolation:** `TfidfVectorizer.fit()` is strictly executed on `X_train`. Under no circumstances may `fit()` or `fit_transform()` be called on validation or test sets; only `transform()` is permitted.
2. **Threshold Isolation:** Classification decision thresholds (e.g. boundary between `likely safe` and `needs review`) are optimized strictly using validation split precision-recall curves. The held-out test set is never inspected to adjust thresholds.
3. **Data Deduplication:** A hash-based deduplication step in `scripts/prepare_data.py` ensures identical messages or near-identical templates do not appear simultaneously across train and test sets.

---

## 3. Class Imbalance Handling

Scam detection naturally exhibits class imbalance (benign messages typically outnumber scams in real-world streams).
- **Technique 1: Class Weight Balancing:** In `LogisticRegression(class_weight='balanced')`, penalty weights are inversely proportional to class frequencies.
- **Technique 2: Stratified Sampling:** Preserves label distribution across splits to avoid unrepresentative validation folds.
- **Technique 3: Balanced Evaluation Metrics:** Avoid reliance on raw Accuracy. Prioritize Macro F1, Precision, Recall, and Area Under the ROC Curve (ROC-AUC).

---

## 4. Evaluation Metrics & Error Investigation Protocol

### 4.1 Target Performance Criteria (Distinct from Measured Results)
*Note: The following values represent target engineering goals for model validation, not fabricated measurements. Actual measured results will be recorded upon Phase 8 execution.*

| Metric | Target Minimum | Target Desired | Justification |
| :--- | :--- | :--- | :--- |
| **Precision (Scam)** | ≥ 0.90 | ≥ 0.94 | Minimizes false alarms on important benign communications (e.g., actual bank OTPs). |
| **Recall (Scam)** | ≥ 0.88 | ≥ 0.93 | Ensures genuine phishing lures and malicious links are caught. |
| **Macro F1-Score** | ≥ 0.88 | ≥ 0.92 | Harmonic mean balancing both classes equally. |
| **Inference Latency** | ≤ 50 ms | ≤ 20 ms | Guarantees instant real-time feedback on user submissions. |

### 4.2 Confusion Matrix Layout
The evaluation script `scripts/evaluate.py` will generate and export the 2x2 confusion matrix:
```text
                  Predicted Safe (0)      Predicted Scam (1)
Actual Safe (0)   True Negative (TN)      False Positive (FP) [Type I Error]
Actual Scam (1)   False Negative (FN)     True Positive (TP)  [Type II Error]
```

### 4.3 False Positive & False Negative Investigation Protocol
During Phase 8 evaluation, all misclassified test instances are systematically logged to `docs/EVALUATION_REPORT.md` with the following root-cause analysis:
1. **False Positive (FP) Analysis (Benign flagged as Scam):**
   - Check if message contains commercial urgency keywords ("Hurry!", "Limited Offer", "Sale ends today").
   - Check if URL uses promotional domains with high entropy or generic TLDs.
   - *Mitigation:* Adjust n-gram feature vocabulary; add negative-weight indicators for authenticated sender signatures.
2. **False Negative (FN) Analysis (Scam missed by system):**
   - Check if scam uses conversational lures ("Hi mom, I lost my phone") without traditional financial keywords.
   - Check if URL uses brand-new evasive obfuscation or legitimate cloud hosting (e.g. `docs.google.com`, `firebaseapp.com`).
   - *Mitigation:* Expand training set with social-engineering lures; enhance lexical subdomain-depth checks.

---

## 5. Automated Unit & Integration Test Suites

### 5.1 Test Suite Structure (`tests/`)

```text
tests/
├── test_sanity.py           # Environment, imports, and config verification
├── test_data_pipeline.py    # Split proportions, zero overlap, deduplication
├── test_url_analyzer.py     # Heuristics: IP addresses, TLDs, homoglyphs, entropy
├── test_text_analyzer.py    # TF-IDF inference, token explainability, boundary lengths
├── test_verdict_arbiter.py  # Scoring policy, dual-mode blending, verdict thresholds
├── test_api.py              # FastAPI endpoints, schemas, status codes, OpenAPI
└── test_security.py         # Malicious input, XSS, SSRF zero-network verification
```

### 5.2 Mandatory Test Cases

#### URL Analyzer Test Cases (`tests/test_url_analyzer.py`)
1. `test_url_ip_address_host`: `http://192.168.1.1/login` -> must flag IP host (+45 risk points).
2. `test_url_homoglyph_punycode`: `http://xn--pypal-4ve.com` -> must flag punycode spoof (+30 points).
3. `test_url_embedded_credentials`: `http://legit.com@phishing-site.xyz/login` -> must flag `@` deception (+35 points).
4. `test_url_high_risk_tld`: `http://secure-verify.click` -> must flag high-risk TLD (+20 points).
5. `test_url_brand_in_subdomain`: `http://paypal.com.verify-account.net` -> must flag brand impersonation (+35 points).
6. `test_url_safe_canonical_domain`: `https://www.google.com` -> must yield low risk score (< 15 points).
7. `test_url_malformed_string`: `htp:/invalid..url` -> must handle gracefully without crashing.

#### Text Analyzer Test Cases (`tests/test_text_analyzer.py`)
1. `test_text_high_risk_urgency`: "URGENT: Your bank account will be closed in 2 hours. Send OTP immediately." -> score ≥ 80.
2. `test_text_benign_message`: "Hey, are we still meeting for lunch at 1 PM today?" -> score ≤ 20.
3. `test_text_explainability_tokens`: Ensure top contributing tokens list is populated with informative tokens (e.g., `["urgent", "otp", "immediately"]`).
4. `test_text_empty_and_whitespace`: Blank or whitespace text returns score 0 and `provided: false`.
5. `test_text_max_length_boundary`: Submitting exactly 10,000 characters runs smoothly without buffer truncation errors.

#### Verdict Arbiter Test Cases (`tests/test_verdict_arbiter.py`)
1. `test_arbiter_both_high_risk`: Both text and URL score > 80 -> verdict is strictly `likely scam`.
2. `test_arbiter_both_low_risk`: Both text and URL score < 20 -> verdict is strictly `likely safe`.
3. `test_arbiter_conflicting_signals`: Safe text + high-risk URL -> verdict escalates to `needs review` or `likely scam` (security-first policy).
4. `test_arbiter_text_only`: Valid text + null URL -> evaluates text score correctly.
5. `test_arbiter_url_only`: Valid URL + null text -> evaluates URL score correctly.

#### API Endpoint Test Cases (`tests/test_api.py`)
1. `test_analyze_valid_payload`: `POST /api/v1/analyze` returns HTTP 200 and schema compliant JSON.
2. `test_analyze_empty_payload`: Both text and url empty -> returns HTTP 422 Unprocessable Entity.
3. `test_health_check`: `GET /api/v1/health` returns HTTP 200 with `status: "healthy"`.
4. `test_evaluation_metrics`: `GET /api/v1/evaluation` returns verified metrics matching `evaluation_meta.json`.

---

## 6. Execution Commands

```bash
# Run entire test suite
pytest -v

# Run targeted unit tests
pytest tests/test_url_analyzer.py -v
pytest tests/test_text_analyzer.py -v
pytest tests/test_verdict_arbiter.py -v

# Run integration tests
pytest tests/test_api.py -v

# Run security tests
pytest tests/test_security.py -v
```
