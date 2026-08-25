from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report


def classification_summary(y_true, y_pred) -> dict:
    accuracy = accuracy_score(y_true, y_pred)
    return {
        "accuracy": accuracy,
        "report": classification_report(y_true, y_pred, zero_division=0),
        "report_dict": classification_report(y_true, y_pred, zero_division=0, output_dict=True),
    }


def expected_calibration_error(y_true, y_pred, confidences: np.ndarray, n_bins: int = 10) -> float:
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
        bin_accuracy   = (y_true[mask] == y_pred[mask]).mean()
        bin_confidence = confidences[mask].mean()
        ece += (mask.sum() / n) * abs(bin_accuracy - bin_confidence)

    return float(ece)


def calibration_breakdown(y_true, y_pred, confidences: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    confidences = np.asarray(confidences)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []

    for low, high in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (confidences >= low) & (confidences < high)
        count = int(mask.sum())
        if count == 0:
            rows.append({"bin_low": round(low, 2), "bin_high": round(high, 2), "count": 0,
                         "mean_confidence": None, "accuracy": None, "gap": None})
            continue
        mean_conf = float(confidences[mask].mean())
        acc = float((y_true[mask] == y_pred[mask]).mean())
        rows.append({
            "bin_low": round(low, 2), "bin_high": round(high, 2), "count": count,
            "mean_confidence": round(mean_conf, 4), "accuracy": round(acc, 4),
            "gap": round(mean_conf - acc, 4),
        })

    return pd.DataFrame(rows)


def per_sample_results(
    descriptions: list[str],
    y_true: list[str],
    y_pred: list[str],
    confidences: np.ndarray,
) -> pd.DataFrame:
    rows = []
    for desc, expected, predicted, conf in zip(descriptions, y_true, y_pred, confidences):
        rows.append({
            "description": desc,
            "expected": expected,
            "predicted": predicted,
            "confidence": round(float(conf), 4),
            "result": "PASS" if expected == predicted else "FAIL",
        })
    return pd.DataFrame(rows)
