"""
Database-backed tools that the Gemini agent can call.

Each function receives a SQLAlchemy Session and returns a plain string
so Gemini can reason over the result naturally.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.transaction_service import create_transaction as _create_transaction


# ── Date helpers ──────────────────────────────────────────────────────────────

def _date_range(period: str):
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    if period == "today":
        start = datetime(now.year, now.month, now.day)
        return start, start + timedelta(days=1)
    if period == "this_week":
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
        return start, start + timedelta(days=7)
    if period == "this_month":
        start = datetime(now.year, now.month, 1)
        end = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
        return start, end
    if period == "last_month":
        start = datetime(now.year - 1, 12, 1) if now.month == 1 else datetime(now.year, now.month - 1, 1)
        end = datetime(now.year, now.month, 1)
        return start, end
    if period == "this_year":
        return datetime(now.year, 1, 1), datetime(now.year + 1, 1, 1)
    return None, None  # all time


# ── Tool functions ────────────────────────────────────────────────────────────

def get_spending_summary(db: Session, period: str = "this_month") -> str:
    """
    Return total income, expenses, and balance for a given period.
    period: today | this_week | this_month | last_month | this_year | all_time
    """
    start, end = _date_range(period)
    filters = []
    if start:
        filters.append(Transaction.transaction_date >= start)
    if end:
        filters.append(Transaction.transaction_date < end)

    income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.transaction_type == "income", *filters
    ).scalar()

    expenses = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.transaction_type == "expense", *filters
    ).scalar()

    income, expenses = float(income), float(expenses)
    period_label = period.replace("_", " ")
    return (
        f"For {period_label}: "
        f"Income ₹{income:.2f}, Expenses ₹{expenses:.2f}, "
        f"Balance ₹{income - expenses:.2f}"
    )


def get_spending_by_category(db: Session, period: str = "this_month", category: str = "") -> str:
    """
    Return expense totals grouped by category, or filtered to one category.
    period: today | this_week | this_month | last_month | this_year | all_time
    category: leave empty for all categories
    """
    start, end = _date_range(period)
    filters = [Transaction.transaction_type == "expense"]
    if start:
        filters.append(Transaction.transaction_date >= start)
    if end:
        filters.append(Transaction.transaction_date < end)
    if category:
        filters.append(Transaction.category.ilike(f"%{category}%"))

    rows = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
        .filter(*filters)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    if not rows:
        label = f"'{category}' " if category else ""
        return f"No {label}expenses found for {period.replace('_', ' ')}."

    period_label = period.replace("_", " ")
    lines = [f"Spending by category ({period_label}):"]
    for cat, total in rows:
        lines.append(f"  {cat or 'uncategorized'}: ₹{float(total):.2f}")
    return "\n".join(lines)


def get_recent_transactions(db: Session, limit: int = 10) -> str:
    """Return the most recent N transactions."""
    limit = max(1, min(limit, 50))
    txns = (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc())
        .limit(limit)
        .all()
    )
    if not txns:
        return "No transactions found."

    lines = [f"Last {len(txns)} transactions:"]
    for t in txns:
        anomaly = " ⚠️" if t.is_anomaly else ""
        lines.append(
            f"  {t.transaction_date.strftime('%d %b %Y')} | "
            f"₹{float(t.amount):.2f} | {t.description} | "
            f"{t.category or 'uncategorized'} | {t.transaction_type}{anomaly}"
        )
    return "\n".join(lines)


def get_anomalies(db: Session) -> str:
    """Return all transactions flagged as anomalies."""
    txns = (
        db.query(Transaction)
        .filter(Transaction.is_anomaly == True)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )
    if not txns:
        return "No anomalous transactions detected."

    lines = [f"Found {len(txns)} unusual transaction(s):"]
    for t in txns:
        lines.append(
            f"  {t.transaction_date.strftime('%d %b %Y')} | "
            f"₹{float(t.amount):.2f} | {t.description} | {t.category}"
        )
        if t.anomaly_reason:
            lines.append(f"    → {t.anomaly_reason}")
    return "\n".join(lines)


def compare_periods(db: Session, category: str, period1: str, period2: str) -> str:
    """
    Compare spending in a category across two periods.
    Useful for questions like 'did I spend more on food this month vs last month?'
    """
    def _total(period: str, cat: str) -> float:
        start, end = _date_range(period)
        filters = [Transaction.transaction_type == "expense"]
        if start:
            filters.append(Transaction.transaction_date >= start)
        if end:
            filters.append(Transaction.transaction_date < end)
        if cat:
            filters.append(Transaction.category.ilike(f"%{cat}%"))
        result = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(*filters).scalar()
        return float(result)

    t1 = _total(period1, category)
    t2 = _total(period2, category)
    diff = t2 - t1
    direction = "more" if diff > 0 else "less"
    cat_label = f"on {category}" if category else "(all categories)"

    return (
        f"Comparison {cat_label}: "
        f"{period1.replace('_', ' ')} = ₹{t1:.2f}, "
        f"{period2.replace('_', ' ')} = ₹{t2:.2f}. "
        f"You spent ₹{abs(diff):.2f} {direction} in {period2.replace('_', ' ')}."
    )


def add_transaction(
    db: Session,
    description: str,
    amount: float,
    transaction_type: str = "expense",
) -> str:
    """
    Add a new transaction. Returns confirmation with category and anomaly warning if applicable.
    transaction_type: expense | income
    """
    if amount <= 0:
        return "Amount must be greater than 0."
    if transaction_type not in ("expense", "income"):
        transaction_type = "expense"

    t = _create_transaction(
        db=db,
        description=description,
        amount=amount,
        transaction_type=transaction_type,
        transaction_date=datetime.now(tz=timezone.utc).replace(tzinfo=None),
    )

    msg = (
        f"Added ₹{float(t.amount):.2f} for '{t.description}' "
        f"under {t.category or 'uncategorized'} ({t.transaction_type})."
    )
    if t.is_anomaly and t.anomaly_reason:
        msg += f" ⚠️ {t.anomaly_reason}"
    return msg
