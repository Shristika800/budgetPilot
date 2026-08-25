from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, le=1_000_000_000, decimal_places=2)
    transaction_type: Literal["income", "expense"]
    transaction_date: datetime

    @field_validator("transaction_date")
    @classmethod
    def no_far_future_dates(cls, v: datetime) -> datetime:
        # Allow up to 1 day ahead to account for timezone differences.
        cutoff = datetime.now(tz=timezone.utc).replace(tzinfo=None) + timedelta(days=1)
        if v.replace(tzinfo=None) > cutoff:
            raise ValueError("transaction_date cannot be more than 1 day in the future")
        return v


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: Decimal
    category: str | None
    confidence: float | None
    transaction_type: str
    transaction_date: datetime
    created_at: datetime
    is_anomaly: bool
    anomaly_reason: str | None

    model_config = {
        "from_attributes": True
    }