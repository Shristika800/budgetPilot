"""
ML evaluation script for the BudgetPilot transaction categorizer.

Evaluates the trained model on a held-out test split (not the training data).
Prints per-sample PASS/FAIL results, classification metrics, calibration ECE,
and a threshold coverage table.

Usage
-----
    python ml/evaluation/threshold_test.py

Run this after retraining the model with ml/models/categorizer.py to verify
that accuracy and calibration have improved.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.evaluation.metrics import (
    calibration_breakdown,
    classification_summary,
    expected_calibration_error,
    per_sample_results,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "training_transactions.csv"
MODEL_PATH = BASE_DIR / "ml" / "models" / "transaction_categorizer.joblib"

# Must match the split used during training so we evaluate on truly held-out data.
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Threshold range to sweep
THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

# Spot-check inputs: these test real-world merchant descriptions that previously
# had low confidence.  Format: (description, expected_category)
SPOT_CHECKS = [
    ("blinkit grocery order", "food"),
    ("apollo doctor visit", "health"),
    ("swiggy food order", "food"),
    ("uber ride", "transport"),
    ("netflix subscription", "entertainment"),
    ("electricity bill payment", "utilities"),
    ("amazon shopping", "shopping"),
    ("gym membership", "health"),
    ("salary credited", "other"),
    ("zomato dinner", "food"),
]


def run_evaluation():
    # -----------------------------------------------------------------------
    # Load data + model
    # -----------------------------------------------------------------------
    df = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)

    # Reproduce the exact same train/test split used during training.
    _, X_test, _, y_test = train_test_split(
        df["description"],
        df["category"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df["category"],
    )

    X_test = X_test.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    # -----------------------------------------------------------------------
    # Inference on held-out test set
    # -----------------------------------------------------------------------
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)
    confidences = probabilities.max(axis=1)

    # -----------------------------------------------------------------------
    # Per-sample PASS/FAIL
    # -----------------------------------------------------------------------
    print("=" * 70)
    print("PER-SAMPLE RESULTS (held-out test set)")
    print("=" * 70)

    sample_df = per_sample_results(
        descriptions=X_test.tolist(),
        y_true=y_test.tolist(),
        y_pred=predictions.tolist(),
        confidences=confidences,
    )

    # Print each sample clearly
    for _, row in sample_df.iterrows():
        status = "✓ PASS" if row["result"] == "PASS" else "✗ FAIL"
        print(
            f"{status}  conf={row['confidence']:.3f}  "
            f"expected={row['expected']:<15} predicted={row['predicted']:<15}  "
            f"desc={row['description'][:50]}"
        )

    pass_count = (sample_df["result"] == "PASS").sum()
    fail_count = (sample_df["result"] == "FAIL").sum()
    print(f"\nTotal: {pass_count} PASS  /  {fail_count} FAIL  /  {len(sample_df)} samples")

    # -----------------------------------------------------------------------
    # Classification metrics
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CLASSIFICATION METRICS")
    print("=" * 70)

    summary = classification_summary(y_test.tolist(), predictions.tolist())
    print(f"Accuracy: {summary['accuracy']:.4f}")
    print()
    print(summary["report"])

    # -----------------------------------------------------------------------
    # Calibration
    # -----------------------------------------------------------------------
    print("=" * 70)
    print("CALIBRATION ANALYSIS")
    print("=" * 70)

    ece = expected_calibration_error(
        y_test.tolist(), predictions.tolist(), confidences
    )
    print(f"Expected Calibration Error (ECE): {ece:.4f}")
    print("  (< 0.05 = well-calibrated, < 0.10 = acceptable)")
    print()

    cal_df = calibration_breakdown(
        y_test.tolist(), predictions.tolist(), confidences
    )
    print(cal_df.to_string(index=False))

    # -----------------------------------------------------------------------
    # Threshold sweep (on held-out test set — no train-set leakage)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("THRESHOLD SWEEP (held-out test set)")
    print("=" * 70)
    print(
        f"{'Threshold':>10}  {'Accuracy':>10}  "
        f"{'Coverage':>10}  {'Uncategorized':>14}"
    )
    print("-" * 50)

    for threshold in THRESHOLDS:
        accepted = confidences >= threshold

        if accepted.sum() == 0:
            print(f"{threshold:>10.2f}  {'N/A':>10}  {0:>9.1%}  {len(confidences):>14}")
            continue

        accepted_accuracy = (
            (y_test[accepted].values == predictions[accepted]).mean()
        )
        coverage = accepted.mean()
        uncategorized = (~accepted).sum()

        print(
            f"{threshold:>10.2f}  {accepted_accuracy:>10.4f}  "
            f"{coverage:>9.1%}  {uncategorized:>14}"
        )

    # -----------------------------------------------------------------------
    # Spot-check: specific merchant descriptions
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SPOT-CHECK: REAL-WORLD MERCHANT DESCRIPTIONS")
    print("=" * 70)
    print(
        f"{'Description':<35}  {'Expected':<15}  "
        f"{'Predicted':<15}  {'Conf':>6}  {'Result':>6}"
    )
    print("-" * 85)

    spot_pass = 0
    spot_fail = 0

    for description, expected in SPOT_CHECKS:
        pred = model.predict([description])[0]
        proba = model.predict_proba([description])[0]
        conf = float(proba.max())
        result = "PASS" if pred == expected else "FAIL"

        if result == "PASS":
            spot_pass += 1
        else:
            spot_fail += 1

        marker = "✓" if result == "PASS" else "✗"
        print(
            f"{marker} {description:<33}  {expected:<15}  "
            f"{pred:<15}  {conf:>6.3f}  {result:>6}"
        )

    print(f"\nSpot-check: {spot_pass} PASS  /  {spot_fail} FAIL  /  {len(SPOT_CHECKS)} checks")


if __name__ == "__main__":
    run_evaluation()
