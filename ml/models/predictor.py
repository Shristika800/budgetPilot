from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "transaction_categorizer.joblib"

_model = None


def load_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Train the model first."
            )

        _model = joblib.load(MODEL_PATH)

    return _model


def predict_category(description: str):
    model = load_model()

    prediction = model.predict([description])[0]
    probabilities = model.predict_proba([description])[0]

    confidence = float(probabilities.max())

    if confidence < 0.40:
        prediction = "uncategorized"

    return {
        "category": prediction,
        "confidence": confidence,
    }