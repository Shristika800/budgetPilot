from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from ml.models.predictor import predict_category


def create_transaction(
    db: Session,
    description: str,
    amount: float,
    transaction_type: str,
    transaction_date,
):
    # Pass transaction_type so income transactions skip the expense categorizer.
    prediction = predict_category(description, transaction_type=transaction_type)

    transaction = Transaction(
        description=description,
        amount=amount,
        category=prediction["category"],
        confidence=prediction["confidence"],
        transaction_type=transaction_type,
        transaction_date=transaction_date,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction
