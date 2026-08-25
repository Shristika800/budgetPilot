from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.evaluation.metrics import (
    calibration_breakdown,
    classification_summary,
    expected_calibration_error,
    per_sample_results,
)

BASE_DIR    = Path(__file__).resolve().parents[2]
DATA_PATH   = BASE_DIR / "data" / "training_transactions.csv"
MODEL_PATH  = BASE_DIR / "ml" / "models" / "transaction_categorizer.joblib"

TEST_SIZE    = 0.2
RANDOM_STATE = 42
THRESHOLDS   = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

SPOT_CHECKS = [
    ("blinkit grocery order",    "food"),
    ("apollo doctor visit",      "health"),
    ("swiggy food order",        "food"),
    ("uber ride",                "transport"),
    ("netflix subscription",     "entertainment"),
    ("electricity bill payment", "utilities"),
    ("amazon shopping",          "shopping"),
    ("gym membership",           "health"),
    ("salary credited",          "other"),
    ("zomato dinner",            "food"),
]


def run_evaluation():
    df    = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)

    _, X_test, _, y_test = train_test_split(
        df["description"], df["category"],
        test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df["category"],
    )
    X_test = X_test.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    predictions  = model.predict(X_test)
    probabilities = model.predict_proba(X_test)
    confidences  = probabilities.max(axis=1)

    # Per-sample results
    print("=" * 70)
    print("PER-SAMPLE RESULTS (held-out test set)")
    print("=" * 70)
    sample_df = per_sample_results(X_test.tolist(), y_test.tolist(), predictions.tolist(), confidences)
    for _, row in sample_df.iterrows():
        status = "✓ PASS" if row["result"] == "PASS" else "✗ FAIL"
        print(f"{status}  conf={row['confidence']:.3f}  expected={row['expected']:<15} predicted={row['predicted']:<15}  desc={row['description'][:50]}")
    pass_count = (sample_df["result"] == "PASS").sum()
    fail_count = (sample_df["result"] == "FAIL").sum()
    print(f"\nTotal: {pass_count} PASS  /  {fail_count} FAIL  /  {len(sample_df)} samples")

    # Classification metrics
    print("\n" + "=" * 70)
    print("CLASSIFICATION METRICS")
    print("=" * 70)
    summary = classification_summary(y_test.tolist(), predictions.tolist())
    print(f"Accuracy: {summary['accuracy']:.4f}\n")
    print(summary["report"])

    # Calibration
    print("=" * 70)
    print("CALIBRATION")
    print("=" * 70)
    ece = expected_calibration_error(y_test.tolist(), predictions.tolist(), confidences)
    print(f"ECE: {ece:.4f}  (< 0.05 = well-calibrated)\n")
    print(calibration_breakdown(y_test.tolist(), predictions.tolist(), confidences).to_string(index=False))

    # Threshold sweep
    print("\n" + "=" * 70)
    print("THRESHOLD SWEEP")
    print("=" * 70)
    print(f"{'Threshold':>10}  {'Accuracy':>10}  {'Coverage':>10}  {'Uncategorized':>14}")
    print("-" * 50)
    for threshold in THRESHOLDS:
        accepted = confidences >= threshold
        if accepted.sum() == 0:
            print(f"{threshold:>10.2f}  {'N/A':>10}  {0:>9.1%}  {len(confidences):>14}")
            continue
        acc = (y_test[accepted].values == predictions[accepted]).mean()
        print(f"{threshold:>10.2f}  {acc:>10.4f}  {accepted.mean():>9.1%}  {(~accepted).sum():>14}")

    # Spot checks
    print("\n" + "=" * 70)
    print("SPOT CHECKS")
    print("=" * 70)
    print(f"{'Description':<35}  {'Expected':<15}  {'Predicted':<15}  {'Conf':>6}  {'Result':>6}")
    print("-" * 85)
    spot_pass = spot_fail = 0
    for description, expected in SPOT_CHECKS:
        pred  = model.predict([description])[0]
        conf  = float(model.predict_proba([description])[0].max())
        result = "PASS" if pred == expected else "FAIL"
        spot_pass += result == "PASS"
        spot_fail += result == "FAIL"
        print(f"{'✓' if result == 'PASS' else '✗'} {description:<33}  {expected:<15}  {pred:<15}  {conf:>6.3f}  {result:>6}")
    print(f"\nSpot-check: {spot_pass} PASS  /  {spot_fail} FAIL  /  {len(SPOT_CHECKS)} checks")


if __name__ == "__main__":
    run_evaluation()
