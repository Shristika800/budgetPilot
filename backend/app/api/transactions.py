import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import create_transaction as create_transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    return create_transaction_service(
        db=db,
        description=transaction.description,
        amount=float(transaction.amount),
        transaction_type=transaction.transaction_type,
        transaction_date=transaction.transaction_date,
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Summary ───────────────────────────────────────────────────────────────────

@router.get("/summary")
def get_transaction_summary(db: Session = Depends(get_db)):
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
            {"category": c, "amount": float(t)} for c, t in category_totals
        ],
    }


# ── Trends ────────────────────────────────────────────────────────────────────

@router.get("/trends")
def get_trends(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Returns daily expense totals for the last `days` days.
    Used by the frontend LineChart to show spending over time.
    """
    rows = (
        db.query(
            cast(Transaction.transaction_date, Date).label("date"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.transaction_type == "expense",
            Transaction.transaction_date
            >= func.date("now", f"-{days} days"),
        )
        .group_by(cast(Transaction.transaction_date, Date))
        .order_by(cast(Transaction.transaction_date, Date))
        .all()
    )
    return [
        {"date": str(row.date), "amount": float(row.total)}
        for row in rows
    ]


# ── CSV Import ────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {"description", "amount", "transaction_type", "transaction_date"}


@router.post("/import", status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Bulk-import transactions from a CSV file.

    Expected columns: description, amount, transaction_type, transaction_date
    transaction_date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    transaction_type: income | expense

    The ML categorizer runs on every imported row automatically.
    Returns a summary of how many rows were imported vs skipped.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM from Excel exports
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))

    # Validate headers
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # row 1 = header
        try:
            description = row["description"].strip()
            if not description or len(description) > 500:
                raise ValueError("description is empty or too long")

            amount = float(row["amount"].strip())
            if amount <= 0:
                raise ValueError("amount must be > 0")

            tx_type = row["transaction_type"].strip().lower()
            if tx_type not in ("income", "expense"):
                raise ValueError("transaction_type must be 'income' or 'expense'")

            date_str = row["transaction_date"].strip()
            # Accept YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    tx_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Cannot parse date: {date_str!r}")

            create_transaction_service(
                db=db,
                description=description,
                amount=amount,
                transaction_type=tx_type,
                transaction_date=tx_date,
            )
            imported += 1

        except Exception as exc:
            skipped += 1
            if len(errors) < 10:  # cap error list to avoid huge responses
                errors.append({"row": i, "error": str(exc)})

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
