from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "training_transactions.csv"
MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_PATH = MODEL_DIR / "transaction_categorizer.joblib"


def train_model():
    df = pd.read_csv(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        df["description"],
        df["category"],
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )

    # TF-IDF improvements:
    # - sublinear_tf=True compresses high-frequency term weights (log scale),
    #   which helps rare but meaningful tokens like merchant names get more weight.
    # - min_df=1 keeps all tokens given our small dataset.
    # - max_features caps vocabulary to avoid overfitting on noise.
    tfidf = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_features=5000,
    )

    # CalibratedClassifierCV wraps the base LogisticRegression with Platt scaling
    # (method="sigmoid") using 5-fold cross-validation so that predict_proba()
    # outputs are calibrated probabilities rather than raw softmax scores.
    # This directly fixes the low-confidence issue: a confidence of 0.70 will
    # actually mean the model is right ~70% of the time.
    base_classifier = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver="lbfgs",
    )

    calibrated_classifier = CalibratedClassifierCV(
        estimator=base_classifier,
        method="sigmoid",
        cv=5,
    )

    pipeline = Pipeline(
        [
            ("tfidf", tfidf),
            ("classifier", calibrated_classifier),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)
    confidence = probabilities.max(axis=1)

    accuracy = accuracy_score(y_test, predictions)

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")
    print(f"Accuracy:         {accuracy:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions, labels=pipeline.classes_))

    print("\nClasses:")
    print(pipeline.classes_)

    print(f"\nMean confidence on test set: {confidence.mean():.4f}")
    print(f"Min  confidence on test set: {confidence.min():.4f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
