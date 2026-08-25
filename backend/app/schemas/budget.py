from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    monthly_limit: Decimal = Field(gt=0, le=1_000_000_000, decimal_places=2)


class BudgetUpdate(BaseModel):
    monthly_limit: Decimal = Field(gt=0, le=1_000_000_000, decimal_places=2)


class BudgetResponse(BaseModel):
    id: int
    category: str
    monthly_limit: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetProgress(BaseModel):
    """Budget + current month's spending for that category."""
    id: int
    category: str
    monthly_limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: float  # 0.0–100.0+

    model_config = {"from_attributes": True}
