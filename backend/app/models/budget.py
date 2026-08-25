from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # The spending category this budget applies to (e.g. "food", "shopping")
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    # Monthly budget limit in rupees
    monthly_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=timezone.utc).replace(tzinfo=None),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(tz=timezone.utc).replace(tzinfo=None),
    )

    __table_args__ = (
        # One budget per category — enforced at DB level
        UniqueConstraint("category", name="uq_budget_category"),
        CheckConstraint("monthly_limit > 0", name="ck_budget_limit_positive"),
    )
