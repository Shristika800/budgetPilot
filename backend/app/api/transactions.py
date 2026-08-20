from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.dependencies import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import create_transaction as create_transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    return create_transaction_service(
        db=db,
        description=transaction.description,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        transaction_date=transaction.transaction_date,
    )


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )


@router.get("/summary")
def get_transaction_summary(
    db: Session = Depends(get_db),
):
    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_type == "income")
        .scalar()
    )

    total_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.transaction_type == "expense")
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
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "balance": float(total_income - total_expenses),
        "spending_by_category": [
            {
                "category": category,
                "amount": float(total),
            }
            for category, total in category_totals
        ],
    }