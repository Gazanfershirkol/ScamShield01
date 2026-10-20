"""
ScamShield AI — Held-Out Benchmark Evaluation Script

Evaluates the serialized model artifact against the held-out test split
(data/processed/test.csv), computes classification metrics (Accuracy,
Precision, Recall, F1, ROC-AUC), generates the confusion matrix, performs
error analysis, and serializes evaluation_meta.json for the API.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_CSV_PATH = BASE_DIR / "data" / "processed" / "test.csv"
MODEL_PATH = BASE_DIR / "app" / "models" / "text_model.joblib"
EVAL_META_PATH = BASE_DIR / "app" / "models" / "evaluation_meta.json"


def run_evaluation():
    print(f"=== ScamShield AI Held-Out Evaluation ===")
    print(f"Loading test dataset from: {TEST_CSV_PATH}")

    if not TEST_CSV_PATH.exists():
        raise FileNotFoundError(f"Test split not found at {TEST_CSV_PATH}. Run scripts/prepare_data.py first.")

    df_test = pd.read_csv(TEST_CSV_PATH)
    print(f"Test split loaded: {len(df_test)} samples ({sum(df_test['label'] == 0)} benign, {sum(df_test['label'] == 1)} scam).")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}. Run scripts/train.py first.")

    print(f"Loading model bundle from: {MODEL_PATH}")
    bundle = joblib.load(MODEL_PATH)
    vectorizer = bundle["vectorizer"]
    calibrated_model = bundle["calibrated_model"]

    # Transform text and predict probabilities
    X_test_vec = vectorizer.transform(df_test["text"].fillna(""))
    y_true = df_test["label"].values

    # Calibrated probabilities for class 1 (scam)
    y_prob = calibrated_model.predict_proba(X_test_vec)[:, 1]

    # Evaluate at standard decision threshold 0.50
    y_pred = (y_prob >= 0.50).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_prob))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    print("\n--- Empirical Benchmark Metrics ---")
    print(f"Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision: {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:    {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:  {f1:.4f} ({f1*100:.2f}%)")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print("\n--- Confusion Matrix ---")
    print(f"True Negatives (Safe correctly identified):  {tn}")
    print(f"False Positives (Safe misflagged as Scam):  {fp}")
    print(f"False Negatives (Scam missed by system):    {fn}")
    print(f"True Positives (Scam correctly identified): {tp}")

    # Qualitative Error Analysis
    df_test["pred_prob"] = y_prob
    df_test["pred_label"] = y_pred

    fp_samples = df_test[(df_test["label"] == 0) & (df_test["pred_label"] == 1)]
    fn_samples = df_test[(df_test["label"] == 1) & (df_test["pred_label"] == 0)]

    print(f"\nTotal False Positives: {len(fp_samples)}")
    for _, row in fp_samples.head(3).iterrows():
        print(f"  [FP] Prob={row['pred_prob']:.3f} | Category={row['category']} | Text: {row['text'][:80]}...")

    print(f"Total False Negatives: {len(fn_samples)}")
    for _, row in fn_samples.head(3).iterrows():
        print(f"  [FN] Prob={row['pred_prob']:.3f} | Category={row['category']} | Text: {row['text'][:80]}...")

    # Build evaluation_meta.json payload
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    eval_meta = {
        "dataset": {
            "name": "ScamShield Benchmark Dataset (Synthetic + Publicly Licensed Open Datasets)",
            "total_samples": 2500,
            "train_samples": 1750,
            "val_samples": 375,
            "test_samples": 375,
            "stratified": True,
        },
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
        },
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "threshold_strategy": {
            "scam_threshold": 0.75,
            "review_threshold": 0.35,
            "selected_on": "Validation split optimization for balanced F1",
        },
        "verified_at": now_utc,
    }

    EVAL_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVAL_META_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_meta, f, indent=2)

    print(f"\nEvaluation metadata successfully exported to: {EVAL_META_PATH}")
    return eval_meta


if __name__ == "__main__":
    run_evaluation()
