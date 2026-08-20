from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    transaction_type: Literal["income", "expense"]
    transaction_date: datetime


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    category: str | None
    confidence: float | None
    transaction_type: str
    transaction_date: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True
    }