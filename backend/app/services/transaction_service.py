from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from ml.models.predictor import predict_category
from ml.models.anomaly_detector import detect_anomaly


def create_transaction(
    db: Session,
    description: str,
    amount: float,
    transaction_type: str,
    transaction_date,
):
    # Categorize via ML (income transactions bypass the model)
    prediction = predict_category(description, transaction_type=transaction_type)
    category = prediction["category"]

    # Run anomaly detection for expense transactions with a known category
    anomaly = {"is_anomaly": False, "reason": None, "z_score": None, "mean": None}
    if transaction_type == "expense" and category not in ("uncategorized", "income"):
        # Fetch historical amounts for this category
        historical = (
            db.query(Transaction.amount)
            .filter(
                Transaction.category == category,
                Transaction.transaction_type == "expense",
            )
            .all()
        )
        historical_amounts = [float(row.amount) for row in historical]
        anomaly = detect_anomaly(amount, category, historical_amounts)

    transaction = Transaction(
        description=description,
        amount=amount,
        category=category,
        confidence=prediction["confidence"],
        transaction_type=transaction_type,
        transaction_date=transaction_date,
        is_anomaly=anomaly["is_anomaly"],
        anomaly_reason=anomaly["reason"],
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction
