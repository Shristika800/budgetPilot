from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "transaction_categorizer.joblib"


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Train the model first."
        )

    return joblib.load(MODEL_PATH)


def predict_category(description: str):
    model = load_model()

    prediction = model.predict([description])[0]
    probabilities = model.predict_proba([description])[0]

    confidence = float(probabilities.max())

    return {
        "category": prediction,
        "confidence": confidence,
    }
