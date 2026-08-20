from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def get_summary(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    query_filter = []

    if start_date:
        query_filter.append(Transaction.transaction_date >= start_date)

    if end_date:
        query_filter.append(Transaction.transaction_date < end_date)

    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.transaction_type == "income",
            *query_filter,
        )
        .scalar()
    )

    total_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.transaction_type == "expense",
            *query_filter,
        )
        .scalar()
    )

    category_totals = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.transaction_type == "expense",
            Transaction.category.isnot(None),
            *query_filter,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "net": float(total_income - total_expenses),
        "spending_by_category": [
            {
                "category": category,
                "amount": float(total),
            }
            for category, total in category_totals
        ],
    }