"""
ScamShield AI — Model Training and Calibration Pipeline

This script:
1. Loads training (train.csv) and validation (val.csv) partitions from data/processed/.
2. Fits TfidfVectorizer(ngram_range=(1, 2), max_features=5000) STRICTLY on train data.
3. Trains LogisticRegression with balanced class weights (random_state=42).
4. Calibrates probability estimates using Platt scaling on the validation split.
5. Computes validation performance metrics (Accuracy, Precision, Recall, F1, ROC-AUC).
6. Serializes the trained pipeline, feature weights, and metadata to app/models/text_model.joblib.
"""

from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "app" / "models"
MODEL_PATH = MODEL_DIR / "text_model.joblib"

TRAIN_FILE = PROCESSED_DATA_DIR / "train.csv"
VAL_FILE = PROCESSED_DATA_DIR / "val.csv"


def train_model() -> Path:
    """
    Executes the training and probability calibration pipeline and exports
    the serialized model bundle.
    """
    print("=" * 70)
    print("ScamShield AI — Text Model Training & Probability Calibration")
    print("=" * 70)

    # 1. Load data
    assert TRAIN_FILE.exists(), f"Missing train split: {TRAIN_FILE}"
    assert VAL_FILE.exists(), f"Missing val split: {VAL_FILE}"

    train_df = pd.read_csv(TRAIN_FILE)
    val_df = pd.read_csv(VAL_FILE)

    X_train = train_df["text"].astype(str)
    y_train = train_df["label"].astype(int)

    X_val = val_df["text"].astype(str)
    y_val = val_df["label"].astype(int)

    print(f"\n[1/5] Loaded data splits:")
    print(f" -> Train: {len(X_train)} samples ({y_train.mean():.1%} scam)")
    print(f" -> Val:   {len(X_val)} samples ({y_val.mean():.1%} scam)")

    # 2. Fit TF-IDF Vectorizer strictly on X_train (Leakage Prevention)
    print("\n[2/5] Fitting TF-IDF Vectorizer (ngram_range=(1,2), max_features=5000)...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_features=5000,
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)

    vocab_size = len(vectorizer.vocabulary_)
    print(f" -> Vocabulary extracted: {vocab_size} unique n-gram features.")

    # 3. Fit Base Logistic Regression Classifier
    print("\n[3/5] Training base LogisticRegression model (class_weight='balanced', seed=42)...")
    base_clf = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )
    base_clf.fit(X_train_vec, y_train)
    print(" -> Base model training complete.")

    # 4. Calibrate Probabilities using 5-Fold Cross-Validation on Training Split
    print("\n[4/5] Calibrating probabilities via CalibratedClassifierCV (cv=5, method='sigmoid')...")
    calibrated_clf = CalibratedClassifierCV(
        estimator=base_clf,
        method="sigmoid",
        cv=5
    )
    calibrated_clf.fit(X_train_vec, y_train)

    # Evaluate validation metrics
    val_preds = calibrated_clf.predict(X_val_vec)
    val_probs = calibrated_clf.predict_proba(X_val_vec)[:, 1]

    acc = accuracy_score(y_val, val_preds)
    prec = precision_score(y_val, val_preds, zero_division=0)
    rec = recall_score(y_val, val_preds, zero_division=0)
    f1 = f1_score(y_val, val_preds, zero_division=0)
    roc_auc = roc_auc_score(y_val, val_probs)
    cm = confusion_matrix(y_val, val_preds)

    print(f"\nValidation Performance Metrics:")
    print(f" -> Accuracy:  {acc:.4f}")
    print(f" -> Precision: {prec:.4f}")
    print(f" -> Recall:    {rec:.4f}")
    print(f" -> F1-Score:  {f1:.4f}")
    print(f" -> ROC-AUC:   {roc_auc:.4f}")
    print(f" -> Confusion Matrix:\n{cm}")

    # 5. Export Serialized Model Bundle
    print(f"\n[5/5] Serializing model bundle to {MODEL_PATH}...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    feature_names = vectorizer.get_feature_names_out()
    bundle = {
        "vectorizer": vectorizer,
        "calibrated_model": calibrated_clf,
        "base_classifier": base_clf,
        "feature_names": feature_names,
        "vocabulary_size": vocab_size,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "metrics": {
            "val_accuracy": round(float(acc), 4),
            "val_precision": round(float(prec), 4),
            "val_recall": round(float(rec), 4),
            "val_f1": round(float(f1), 4),
            "val_roc_auc": round(float(roc_auc), 4),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    joblib.dump(bundle, MODEL_PATH)
    print(f" -> Model successfully serialized ({MODEL_PATH.stat().st_size / 1024:.1f} KB).")

    print("\n" + "=" * 70)
    print("Phase 4 Model Training Pipeline COMPLETE.")
    print("=" * 70)

    return MODEL_PATH


if __name__ == "__main__":
    train_model()
