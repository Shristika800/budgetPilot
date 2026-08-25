from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "transaction_categorizer.joblib"

# Confidence threshold: predictions below this become "uncategorized".
# With CalibratedClassifierCV a confidence of 0.30 means the model is
# correct ~30% of the time, so 0.30 is a reasonable floor that keeps
# coverage high while filtering out near-random guesses.
# Revisit after running ml/evaluation/threshold_test.py to pick the
# threshold that best balances accuracy and coverage on held-out data.
CONFIDENCE_THRESHOLD = 0.30

# Categories that represent income — the expense categorizer should not
# run on these since the model was trained exclusively on expense data.
INCOME_KEYWORDS = {
    "salary",
    "income",
    "earned",
    "received",
    "credited",
    "bonus",
    "refund",
    "reimbursement",
}

_model = None


def load_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run 'python ml/models/categorizer.py' to train it first."
            )
        _model = joblib.load(MODEL_PATH)

    return _model


def _is_income(description: str) -> bool:
    """Return True if the description looks like an income transaction."""
    tokens = description.lower().split()
    return bool(INCOME_KEYWORDS.intersection(tokens))


def predict_category(description: str, transaction_type: str = "expense") -> dict:
    """
    Predict the spending category for a transaction description.

    Parameters
    ----------
    description      : raw transaction description string
    transaction_type : "expense" or "income"
                       Income transactions bypass the ML model entirely.

    Returns
    -------
    dict with keys:
        "category"   -- predicted category string, or "uncategorized"
        "confidence" -- calibrated probability (0.0–1.0)
    """
    # Skip the expense categorizer for income transactions.
    if transaction_type == "income" or _is_income(description):
        return {"category": "income", "confidence": 1.0}

    try:
        model = load_model()
    except FileNotFoundError as exc:
        # Degrade gracefully — log the error but don't crash the API.
        import logging
        logging.getLogger(__name__).error("ML model unavailable: %s", exc)
        return {"category": "uncategorized", "confidence": 0.0}

    prediction = model.predict([description])[0]
    probabilities = model.predict_proba([description])[0]
    confidence = float(probabilities.max())

    if confidence < CONFIDENCE_THRESHOLD:
        prediction = "uncategorized"

    return {
        "category": prediction,
        "confidence": confidence,
    }
