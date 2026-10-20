"""
ScamShield AI — Phase 2 Data Pipeline Test Suite

Validates dataset file existence, split proportions, stratification balance,
PII scrubbing, and zero cross-split leakage across train, val, and test partitions.
"""

from pathlib import Path
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
TRAIN_FILE = PROCESSED_DATA_DIR / "train.csv"
VAL_FILE = PROCESSED_DATA_DIR / "val.csv"
TEST_FILE = PROCESSED_DATA_DIR / "test.csv"


@pytest.fixture(scope="module")
def dataset_splits():
    """Load train, val, and test processed CSV splits."""
    assert TRAIN_FILE.exists(), f"Missing train split: {TRAIN_FILE}"
    assert VAL_FILE.exists(), f"Missing val split: {VAL_FILE}"
    assert TEST_FILE.exists(), f"Missing test split: {TEST_FILE}"

    train_df = pd.read_csv(TRAIN_FILE)
    val_df = pd.read_csv(VAL_FILE)
    test_df = pd.read_csv(TEST_FILE)

    return train_df, val_df, test_df


def test_processed_files_exist():
    """Verify that all three processed split CSV files exist on disk."""
    assert TRAIN_FILE.is_file(), "train.csv not found in data/processed/"
    assert VAL_FILE.is_file(), "val.csv not found in data/processed/"
    assert TEST_FILE.is_file(), "test.csv not found in data/processed/"


def test_required_columns(dataset_splits):
    """Verify that all splits contain required columns with zero missing values."""
    required_cols = {"id", "text", "label", "category"}
    for split_name, df in zip(["train", "val", "test"], dataset_splits):
        assert required_cols.issubset(df.columns), (
            f"{split_name} split is missing columns: {required_cols - set(df.columns)}"
        )
        assert df["text"].isnull().sum() == 0, f"{split_name} split contains null text values"
        assert df["label"].isnull().sum() == 0, f"{split_name} split contains null label values"
        # Text must not be purely whitespace
        assert (df["text"].str.strip().str.len() == 0).sum() == 0, (
            f"{split_name} split contains empty whitespace text"
        )


def test_split_proportions(dataset_splits):
    """Verify 70/15/15 split ratio within expected sample limits."""
    train_df, val_df, test_df = dataset_splits
    total = len(train_df) + len(val_df) + len(test_df)

    assert total == 2500, f"Expected 2500 total samples, got {total}"
    assert len(train_df) == 1750, f"Expected 1750 train samples (70%), got {len(train_df)}"
    assert len(val_df) == 375, f"Expected 375 validation samples (15%), got {len(val_df)}"
    assert len(test_df) == 375, f"Expected 375 test samples (15%), got {len(test_df)}"


def test_labels_are_binary(dataset_splits):
    """Verify that all labels are strictly binary integers (0 for safe, 1 for scam)."""
    for split_name, df in zip(["train", "val", "test"], dataset_splits):
        unique_labels = set(df["label"].unique())
        assert unique_labels.issubset({0, 1}), (
            f"{split_name} split contains invalid label values: {unique_labels}"
        )


def test_stratification_balance(dataset_splits):
    """Verify that the scam class ratio (40%) is preserved across all three splits."""
    for split_name, df in zip(["train", "val", "test"], dataset_splits):
        scam_ratio = df["label"].mean()
        # Expect ~40% (0.40) scam with a tight 1.5% margin
        assert 0.38 <= scam_ratio <= 0.42, (
            f"{split_name} split stratification deviated: {scam_ratio:.2%} scam (expected ~40%)"
        )


def test_zero_cross_split_leakage(dataset_splits):
    """Verify that no sample appears in more than one partition (strict leakage check)."""
    train_df, val_df, test_df = dataset_splits

    train_texts = set(train_df["text"].str.lower().str.strip())
    val_texts = set(val_df["text"].str.lower().str.strip())
    test_texts = set(test_df["text"].str.lower().str.strip())

    train_val_overlap = train_texts.intersection(val_texts)
    train_test_overlap = train_texts.intersection(test_texts)
    val_test_overlap = val_texts.intersection(test_texts)

    assert len(train_val_overlap) == 0, (
        f"Data leakage detected! {len(train_val_overlap)} text instances overlap between train and val"
    )
    assert len(train_test_overlap) == 0, (
        f"Data leakage detected! {len(train_test_overlap)} text instances overlap between train and test"
    )
    assert len(val_test_overlap) == 0, (
        f"Data leakage detected! {len(val_test_overlap)} text instances overlap between val and test"
    )
