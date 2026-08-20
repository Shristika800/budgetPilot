def detect_intent(message: str) -> str:
    message = message.lower().strip()

    summary_words = [
        "how much",
        "total",
        "balance",
        "summary",
        "spent this month",
        "spending",
    ]

    transaction_list_words = [
        "transactions",
        "recent transactions",
        "my expenses",
        "my spending",
        "show expenses",
    ]

    spending_query_words = [
        "what did i spend",
        "what have i spent",
        "how much did i spend on",
        "how much have i spent on",
        "how much do i spend on",
        "spending on",
        "spent on",
    ]

    transaction_words = [
        "spent",
        "spend",
        "paid",
        "bought",
        "purchase",
        "purchased",
        "earned",
        "received",
        "salary",
        "credited",
    ]

    advice_words = [
    "advice",
    "advise me",
    "budget advice",
    "budgeting advice",
    "how can i save",
    "how should i save",
    "am i spending too much",
    "where am i overspending",
    ]

    if any(word in message for word in advice_words):
        return "advice"

    if any(word in message for word in spending_query_words):
        return "spending_query"

    if any(word in message for word in summary_words):
        return "summary"

    if any(word in message for word in transaction_list_words):
        return "list_transactions"

    if any(word in message for word in transaction_words):
        return "create_transaction"

    return "unknown"