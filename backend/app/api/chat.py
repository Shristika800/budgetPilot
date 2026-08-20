from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.dependencies import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import extract_transaction
from app.services.intent_service import detect_intent
from app.services.summary_service import get_summary
from app.services.data_service import detect_period, get_date_range
from app.services.advice_service import generate_advice
from app.services.transaction_service import create_transaction
from app.models.transaction import Transaction


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    intent = detect_intent(request.message)

    # ADVICE
    if intent == "advice":
        summary = get_summary(db)
        advice = generate_advice(summary)

        return ChatResponse(
            message=advice
        )

    # CREATE TRANSACTION
    if intent == "create_transaction":
        transaction_data = extract_transaction(request.message)

        if transaction_data is None:
            return ChatResponse(
                message="I couldn't find a transaction amount in that message."
            )

        transaction = create_transaction(
            db=db,
            description=transaction_data["description"],
            amount=transaction_data["amount"],
            transaction_type=transaction_data["transaction_type"],
            transaction_date=datetime.utcnow(),
        )

        if transaction.category == "uncategorized":
            message = (
                f"Added ₹{transaction.amount:.2f} "
                f"for {transaction.description}. "
                f"I couldn't confidently categorize it."
            )
        else:
            message = (
                f"Added ₹{transaction.amount:.2f} "
                f"for {transaction.description} "
                f"under {transaction.category}."
            )

        return ChatResponse(
            message=message,
            transaction_id=transaction.id,
        )

    # SUMMARY
    if intent == "summary":
        period = detect_period(request.message)

        start_date, end_date = get_date_range(period)

        summary = get_summary(
            db,
            start_date=start_date,
            end_date=end_date,
        )

        message = (
            f"You've spent ₹{summary['total_expenses']:.2f} "
            f"and received ₹{summary['total_income']:.2f}."
        )

        if summary["spending_by_category"]:
            top_category = summary["spending_by_category"][0]

            message += (
                f" Your biggest spending category is "
                f"{top_category['category']} "
                f"at ₹{top_category['amount']:.2f}."
            )

        return ChatResponse(message=message)

    # SPENDING QUERY
    if intent == "spending_query":
        message = request.message.lower().strip()

        if " on " not in message:
            return ChatResponse(
                message=(
                    "Tell me what you want to check, "
                    "for example: 'How much did I spend on Uber?'"
                )
            )

        keyword = message.split(" on ", 1)[1]
        keyword = keyword.strip(" ?.!,")
        
        # Detect time period
        period = detect_period(message)
        start_date, end_date = get_date_range(period)

        date_filters = []

        if start_date:
            date_filters.append(
                Transaction.transaction_date >= start_date
            )

        if end_date:
            date_filters.append(
                Transaction.transaction_date < end_date
            )

        # Check category first
        category_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.category.ilike(keyword)
            )
            .filter(
                Transaction.transaction_type == "expense"
            )
            .filter(*date_filters)
            .all()
        )

        if category_transactions:
            total = sum(
                transaction.amount
                for transaction in category_transactions
            )

            return ChatResponse(
                message=f"You spent ₹{total:.2f} on {keyword}."
            )

        # Otherwise search transaction descriptions
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.description.ilike(f"%{keyword}%")
            )
            .filter(
                Transaction.transaction_type == "expense"
            )
            .filter(*date_filters)
            .all()
        )

        if not transactions:
            return ChatResponse(
                message=(
                    f"I couldn't find any transactions "
                    f"matching '{keyword}'."
                )
            )

        total = sum(
            transaction.amount
            for transaction in transactions
        )

        return ChatResponse(
            message=f"You spent ₹{total:.2f} on {keyword}."
        )

    # LIST TRANSACTIONS
    if intent == "list_transactions":
        transactions = (
            db.query(Transaction)
            .order_by(Transaction.transaction_date.desc())
            .limit(10)
            .all()
        )

        if not transactions:
            return ChatResponse(
                message="You don't have any transactions yet."
            )

        lines = [
            "Here are your 10 most recent transactions:"
        ]

        for transaction in transactions:
            lines.append(
                f"• ₹{transaction.amount:.2f} — "
                f"{transaction.description} "
                f"({transaction.category})"
            )

        return ChatResponse(
            message="\n".join(lines)
        )

    # FALLBACK
    return ChatResponse(
        message=(
            "I can help you track expenses, "
            "income, and spending."
        )
    )