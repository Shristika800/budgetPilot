from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "transactions.csv"
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

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    print(f"Accuracy: {accuracy:.4f}")

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

    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)

    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
