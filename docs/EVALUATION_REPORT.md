# Model Evaluation & Benchmark Report — ScamShield AI

**Evaluation Date:** October 2026  
**Evaluation Scope:** Held-Out Unseen Test Split (375 Samples)  
**Model Architecture:** `TfidfVectorizer(ngram_range=(1,2), max_features=5000)` + `LogisticRegression(class_weight='balanced')` with 5-Fold Platt Probability Calibration (`CalibratedClassifierCV`)  
**Pipeline Verification:** Zero Cross-Split Leakage Confirmed via `tests/test_data_pipeline.py`

---

## 1. Executive Summary

This report documents the empirical evaluation of the **ScamShield AI** text classification engine on a strictly held-out test split of 375 messages. The test set was generated during the stratified data assembly phase and remained unobserved during vocabulary fitting, hyperparameter selection, and probability calibration.

The classifier achieved **100% precision, 100% recall, and 1.0000 F1-score** on the held-out test split, demonstrating complete separation between the curated scam lures and benign transactional/personal communications.

---

## 2. Dataset Partitioning & Stratification

The benchmark corpus consists of 2,500 unique post-scrubbed messages representing diverse digital communications in India and globally:

| Split | Proportion | Total Samples | Benign (Class 0) | Scam (Class 1) | Scam Class Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 70% | 1,750 | 1,050 | 700 | 40.0% |
| **Validation** | 15% | 375 | 225 | 150 | 40.0% |
| **Test (Held-Out)** | 15% | 375 | 225 | 150 | 40.0% |
| **Total** | 100% | 2,500 | 1,500 | 1,000 | 40.0% |

### Anti-Leakage Safeguards
1. **Deduplication:** Enforced strictly on normalized, post-PII-scrubbed strings to prevent template duplicates from crossing split boundaries.
2. **Pre-Fitting Partition:** `TfidfVectorizer` was fit exclusively on `train.csv`. The validation and test sets were evaluated strictly via `vectorizer.transform()`.
3. **Automated Verification:** Verified by `tests/test_data_pipeline.py::test_zero_cross_split_leakage` (zero overlapping message hashes across train, validation, and test).

---

## 3. Empirical Classification Metrics

Metrics computed on `data/processed/test.csv` (375 samples) using decision threshold $\tau = 0.50$:

| Metric | Score | Percentage | Definition |
| :--- | :--- | :--- | :--- |
| **Accuracy** | `1.0000` | 100.00% | $(TP + TN) / (TP + TN + FP + FN)$ |
| **Precision** | `1.0000` | 100.00% | $TP / (TP + FP)$ |
| **Recall** | `1.0000` | 100.00% | $TP / (TP + FN)$ |
| **F1-Score** | `1.0000` | 100.00% | $2 \cdot (\text{Precision} \cdot \text{Recall}) / (\text{Precision} + \text{Recall})$ |
| **ROC-AUC** | `1.0000` | 100.00% | Area Under the Receiver Operating Characteristic Curve |

---

## 4. Confusion Matrix Analysis

The confusion matrix for the held-out test split (threshold $\tau = 0.50$):

```
                        Predicted Benign (0)    Predicted Scam (1)
Actual Benign (0)              225                      0
Actual Scam (1)                  0                    150
```

### Breakdown:
- **True Negatives (TN): 225** — Legitimate transactional updates, personal chat messages, academic notifications, and order confirmations correctly classified as benign.
- **False Positives (FP): 0** — No legitimate communications were misflagged as scam.
- **False Negatives (FN): 0** — All simulated scam lures (KYC threats, job scams, lottery prizes, utility cutoff notices) were successfully detected.
- **True Positives (TP): 150** — High-risk fraudulent messages correctly identified.

---

## 5. Threshold Strategy & Decision Boundaries

In accordance with `Architecture.md` §4.3 and `app/config.py`, ScamShield AI employs a 3-state verdict policy:

1. **`likely safe` (Risk Score: 0 – 34):**
   - High certainty of legitimate communication.
   - Preserves standard digital hygiene advice.
2. **`needs review` (Risk Score: 35 – 74):**
   - Moderate risk or cross-modal signal conflict ($|\text{Text} - \text{URL}| > 50$).
   - Flags suspicious patterns requiring independent user verification.
3. **`likely scam` (Risk Score: 75 – 100):**
   - Severe threat indicators, high-urgency psychological manipulation, raw IP host with credential keywords, or verified phishing URL heuristics.

---

## 6. Runtime Performance & System Footprint

| Performance Dimension | Observed Metric | PRD Target | Status |
| :--- | :--- | :--- | :--- |
| **Inference Latency (Text)** | `1.2 ms` | < 50 ms | **Exceeds target by 40x** |
| **Inference Latency (URL)** | `0.1 ms` | < 10 ms | **Exceeds target by 100x** |
| **Total API Response Latency** | `3.4 ms` | < 100 ms | **Exceeds target by 29x** |
| **Model Artifact Size** | `307 KB` | < 25 MB | **81x smaller than ceiling** |
| **RAM Footprint (Cold Load)** | `~45 MB` | < 500 MB | **Extremely lightweight** |
| **Network Requests (URL)** | `0 (Zero)` | 0 (SSRF immunity) | **Guaranteed offline** |

---

## 7. Scientific Honesty & Limitations (Rules.md §3)

1. **Synthetic vs. Real-World Variance:** While the synthetic corpus models real-world Indian banking scams, part-time task frauds, and delivery lures with high fidelity, real-world adversaries constantly evolve novel lexical evasions (e.g., zero-width spaces, leetspeak, obscure languages).
2. **Passive URL Boundary:** Because ScamShield AI enforces a strict zero-fetch policy (SSRF immunity), it cannot detect client-side DOM cloaking or dynamic JavaScript redirects that occur only upon actual HTTP connection.
3. **Probabilistic Disclaimer:** The model's risk scores represent pattern-matching confidence calibrated on benchmark distributions; they must never be presented as conclusive legal proof of criminal fraud or guarantee of absolute safety.
