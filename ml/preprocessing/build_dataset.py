from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

ORIGINAL_PATH = BASE_DIR / "data" / "transactions.csv"
EXTERNAL_PATH = BASE_DIR / "data" / "combined_expense_dataset.csv"
OUTPUT_PATH = BASE_DIR / "data" / "training_transactions.csv"


CATEGORY_MAP = {
    "Food & Dining": "food",
    "Shopping": "shopping",
    "Utilities": "utilities",
    "Entertainment": "entertainment",
    "Transport": "transport",
    "Electronics": "electronics",
    "Health": "health",
    "Education": "education",
    "Personal Care": "personal_care",
    "Travel": "travel",
    "Other": "other",
}


def clean_text(value):
    if pd.isna(value):
        return ""

    return " ".join(str(value).strip().lower().split())


def build_dataset():
    original = pd.read_csv(ORIGINAL_PATH)

    original = original[
        ["description", "category"]
    ].copy()

    original["description"] = original["description"].apply(clean_text)
    original["category"] = original["category"].str.strip().str.lower()

    external = pd.read_csv(EXTERNAL_PATH)

    external["category"] = external["category"].map(CATEGORY_MAP)

    external["merchant"] = external["merchant"].apply(clean_text)
    external["description"] = external["description"].apply(clean_text)

    # Combine merchant + description so both provide useful signals.
    external["description"] = (
        external["merchant"] + " " + external["description"]
    ).str.strip()

    external = external[
        ["description", "category"]
    ].dropna(subset=["category"])

    combined = pd.concat(
        [original, external],
        ignore_index=True,
    )

    combined = combined[
        combined["description"].str.len() > 0
    ]

    # Only remove completely identical rows.
    combined = combined.drop_duplicates()

    combined.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Original rows: {len(original)}")
    print(f"External rows: {len(external)}")
    print(f"Combined rows: {len(combined)}")

    print("\nCategory distribution:")
    print(combined["category"].value_counts())

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_dataset()