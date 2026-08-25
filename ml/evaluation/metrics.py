"""
Reusable ML evaluation utilities for the BudgetPilot transaction categorizer.

Functions
---------
classification_summary   -- accuracy + full sklearn classification report
expected_calibration_error (ECE) -- measures how well confidence tracks accuracy
calibration_breakdown    -- per-bin confidence vs accuracy table
per_sample_results       -- DataFrame with prediction, confidence, and PASS/FAIL per row
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------


def classification_summary(
    y_true: list | np.ndarray,
    y_pred: list | np.ndarray,
) -> dict:
    """
    Return a dict with overall accuracy and the full per-class report.

    Parameters
    ----------
    y_true : array-like of str
        Ground-truth category labels.
    y_pred : array-like of str
        Predicted category labels.

    Returns
    -------
    dict with keys:
        "accuracy"  -- float
        "report"    -- str (sklearn classification_report)
        "report_dict" -- dict (machine-readable version of the report)
    """
    accuracy = accuracy_score(y_true, y_pred)
    report_str = classification_report(y_true, y_pred, zero_division=0)
    report_dict = classification_report(
        y_true, y_pred, zero_division=0, output_dict=True
    )

    return {
        "accuracy": accuracy,
        "report": report_str,
        "report_dict": report_dict,
    }


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def expected_calibration_error(
    y_true: list | np.ndarray,
    y_pred: list | np.ndarray,
    confidences: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Compute the Expected Calibration Error (ECE).

    ECE measures the weighted average gap between confidence and accuracy
    across n_bins equal-width buckets.  A perfectly calibrated model has
    ECE = 0.  Values below 0.05 are considered well-calibrated.

    Parameters
    ----------
    y_true      : ground-truth labels
    y_pred      : predicted labels
    confidences : max predict_proba value for each sample (shape: [n_samples])
    n_bins      : number of equal-width bins (default 10)

    Returns
    -------
    float -- ECE score
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    confidences = np.asarray(confidences)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)

    for low, high in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (confidences >= low) & (confidences < high)

        if mask.sum() == 0:
            continue

        bin_accuracy = (y_true[mask] == y_pred[mask]).mean()
        bin_confidence = confidences[mask].mean()
        bin_weight = mask.sum() / n

        ece += bin_weight * abs(bin_accuracy - bin_confidence)

    return float(ece)


def calibration_breakdown(
    y_true: list | np.ndarray,
    y_pred: list | np.ndarray,
    confidences: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Return a per-bin table showing confidence range, sample count,
    mean confidence, and actual accuracy.

    Useful for spotting where the model is over- or under-confident.

    Parameters
    ----------
    Same as expected_calibration_error.

    Returns
    -------
    pd.DataFrame with columns:
        bin_low, bin_high, count, mean_confidence, accuracy, gap
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    confidences = np.asarray(confidences)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []

    for low, high in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (confidences >= low) & (confidences < high)
        count = int(mask.sum())

        if count == 0:
            rows.append(
                {
                    "bin_low": round(low, 2),
                    "bin_high": round(high, 2),
                    "count": 0,
                    "mean_confidence": None,
                    "accuracy": None,
                    "gap": None,
                }
            )
            continue

        mean_conf = float(confidences[mask].mean())
        acc = float((y_true[mask] == y_pred[mask]).mean())

        rows.append(
            {
                "bin_low": round(low, 2),
                "bin_high": round(high, 2),
                "count": count,
                "mean_confidence": round(mean_conf, 4),
                "accuracy": round(acc, 4),
                "gap": round(mean_conf - acc, 4),  # positive = overconfident
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Per-sample results
# ---------------------------------------------------------------------------


def per_sample_results(
    descriptions: list[str],
    y_true: list[str],
    y_pred: list[str],
    confidences: np.ndarray,
) -> pd.DataFrame:
    """
    Build a per-sample DataFrame with description, expected category,
    predicted category, confidence, and a PASS/FAIL column.

    Parameters
    ----------
    descriptions : list of raw description strings
    y_true       : ground-truth category labels
    y_pred       : predicted category labels
    confidences  : max predict_proba value per sample

    Returns
    -------
    pd.DataFrame with columns:
        description, expected, predicted, confidence, result
    """
    results = []

    for desc, expected, predicted, conf in zip(
        descriptions, y_true, y_pred, confidences
    ):
        results.append(
            {
                "description": desc,
                "expected": expected,
                "predicted": predicted,
                "confidence": round(float(conf), 4),
                "result": "PASS" if expected == predicted else "FAIL",
            }
        )

    return pd.DataFrame(results)
