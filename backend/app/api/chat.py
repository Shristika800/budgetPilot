from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.transaction import Transaction
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import extract_transaction
from app.services.data_service import detect_period, get_date_range, strip_period_words
from app.services.intent_service import detect_intent
from app.services.llm_service import ask_gemini
from app.services.summary_service import get_summary
from app.services.transaction_service import create_transaction

router = APIRouter(prefix="/chat", tags=["Chat"])


def _build_financial_context(db: Session) -> str:
    """
    Build a short text summary of the user's finances to inject into the
    Gemini prompt so it can answer questions grounded in real data.
    """
    summary = get_summary(db)

    # Recent 10 transactions
    recent = (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc())
        .limit(10)
        .all()
    )

    lines = [
        f"Total income (all time): ₹{summary['total_income']:.2f}",
        f"Total expenses (all time): ₹{summary['total_expenses']:.2f}",
        f"Balance: ₹{summary['net']:.2f}",
        "",
        "Spending by category (all time):",
    ]
    for item in summary["spending_by_category"]:
        lines.append(f"  - {item['category']}: ₹{item['amount']:.2f}")

    lines.append("")
    lines.append("Last 10 transactions:")
    for t in recent:
        lines.append(
            f"  - {t.transaction_date.strftime('%Y-%m-%d')} | "
            f"₹{float(t.amount):.2f} | {t.description} | "
            f"{t.category or 'uncategorized'} | {t.transaction_type}"
        )

    return "\n".join(lines)


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    intent = detect_intent(request.message)

    # ── CREATE TRANSACTION ────────────────────────────────────────────────────
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
            transaction_date=datetime.now(tz=timezone.utc).replace(tzinfo=None),
        )

        if transaction.category == "uncategorized":
            message = (
                f"Added ₹{float(transaction.amount):.2f} for "
                f"'{transaction.description}'. I couldn't confidently categorize it."
            )
        else:
            message = (
                f"Added ₹{float(transaction.amount):.2f} for "
                f"'{transaction.description}' under {transaction.category}."
            )

        # Surface anomaly warning if detected
        if transaction.is_anomaly and transaction.anomaly_reason:
            message += f"\n\n⚠️ {transaction.anomaly_reason}"

        return ChatResponse(message=message, transaction_id=transaction.id)

    # ── SPENDING QUERY ────────────────────────────────────────────────────────
    if intent == "spending_query":
        msg_lower = request.message.lower().strip()

        if " on " not in msg_lower:
            return ChatResponse(
                message="Tell me what you want to check, e.g. 'How much did I spend on food?'"
            )

        keyword = msg_lower.split(" on ", 1)[1].strip(" ?.!,")
        period = detect_period(msg_lower)
        keyword = strip_period_words(keyword)

        if not keyword:
            return ChatResponse(
                message="Tell me what you want to check, e.g. 'How much did I spend on food?'"
            )

        start_date, end_date = get_date_range(period)
        date_filters = []
        if start_date:
            date_filters.append(Transaction.transaction_date >= start_date)
        if end_date:
            date_filters.append(Transaction.transaction_date < end_date)

        safe_keyword = keyword.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")

        # Try exact category match first
        category_txns = (
            db.query(Transaction)
            .filter(
                Transaction.category.ilike(safe_keyword, escape="\\"),
                Transaction.transaction_type == "expense",
                *date_filters,
            )
            .all()
        )

        if category_txns:
            total = sum(float(t.amount) for t in category_txns)
            return ChatResponse(message=f"You spent ₹{total:.2f} on {keyword}.")

        # Fall back to description search
        desc_txns = (
            db.query(Transaction)
            .filter(
                Transaction.description.ilike(f"%{safe_keyword}%", escape="\\"),
                Transaction.transaction_type == "expense",
                *date_filters,
            )
            .all()
        )

        if not desc_txns:
            return ChatResponse(
                message=f"I couldn't find any transactions matching '{keyword}'."
            )

        total = sum(float(t.amount) for t in desc_txns)
        return ChatResponse(message=f"You spent ₹{total:.2f} on {keyword}.")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    if intent == "summary":
        period = detect_period(request.message)
        start_date, end_date = get_date_range(period)
        summary = get_summary(db, start_date=start_date, end_date=end_date)

        message = (
            f"You've spent ₹{summary['total_expenses']:.2f} "
            f"and received ₹{summary['total_income']:.2f}."
        )
        if summary["spending_by_category"]:
            top = summary["spending_by_category"][0]
            message += (
                f" Your biggest category is {top['category']} "
                f"at ₹{top['amount']:.2f}."
            )
        return ChatResponse(message=message)

    # ── LIST TRANSACTIONS ─────────────────────────────────────────────────────
    if intent == "list_transactions":
        transactions = (
            db.query(Transaction)
            .order_by(Transaction.transaction_date.desc())
            .limit(10)
            .all()
        )
        if not transactions:
            return ChatResponse(message="You don't have any transactions yet.")

        lines = ["Here are your 10 most recent transactions:"]
        for t in transactions:
            lines.append(
                f"• ₹{float(t.amount):.2f} — {t.description} ({t.category or '—'})"
            )
        return ChatResponse(message="\n".join(lines))

    # ── ADVICE + UNKNOWN → GEMINI ─────────────────────────────────────────────
    # For advice requests AND anything the rule-based system can't handle,
    # fall through to Gemini with the user's full financial context injected.
    context = _build_financial_context(db)
    response_text = ask_gemini(request.message, context)
    return ChatResponse(message=response_text)
