from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Numeric(12, 2) avoids IEEE 754 floating-point precision errors
    # that Float would introduce for financial amounts.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=timezone.utc).replace(tzinfo=None),
    )

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transaction_type",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_amount_positive",
        ),
    )
