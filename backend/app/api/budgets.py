from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetResponse, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _current_month_bounds():
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    return start, end


@router.get("/", response_model=list[BudgetProgress])
def get_budgets(db: Session = Depends(get_db)):
    budgets = db.query(Budget).order_by(Budget.category).all()
    start, end = _current_month_bounds()

    result = []
    for budget in budgets:
        spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.category == budget.category,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= start,
                Transaction.transaction_date < end,
            )
            .scalar()
        )
        spent = Decimal(str(spent))
        limit = Decimal(str(budget.monthly_limit))
        remaining = limit - spent
        percent_used = float((spent / limit * 100) if limit > 0 else 0)

        result.append(
            BudgetProgress(
                id=budget.id,
                category=budget.category,
                monthly_limit=limit,
                spent=spent,
                remaining=remaining,
                percent_used=round(percent_used, 1),
            )
        )
    return result


@router.post("/", response_model=BudgetResponse, status_code=201)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db)):
    existing = db.query(Budget).filter(Budget.category == payload.category).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A budget for '{payload.category}' already exists. Use PUT to update it.",
        )
    budget = Budget(
        category=payload.category,
        monthly_limit=float(payload.monthly_limit),
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(budget_id: int, payload: BudgetUpdate, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    budget.monthly_limit = float(payload.monthly_limit)
    budget.updated_at = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    db.delete(budget)
    db.commit()
