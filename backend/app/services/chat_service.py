import re


def extract_transaction(message: str):
    # 1. Prefer currency-prefixed amounts
    currency_match = re.search(
        r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)",
        message,
        re.IGNORECASE,
    )

    if currency_match:
        amount_match = currency_match
    else:
        # 2. Prefer numbers that follow common amount words
        contextual_match = re.search(
            r"(?:for|spent|paid|cost|amount|worth)\s+"
            r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
            message,
            re.IGNORECASE,
        )

        if contextual_match:
            amount_match = contextual_match
        else:
            # 3. Fallback: use the last number
            numbers = list(
                re.finditer(
                    r"\d+(?:\.\d+)?",
                    message,
                )
            )

            if not numbers:
                return None

            amount_match = numbers[-1]

    amount = float(amount_match.group(1))

    message_lower = message.lower()

    income_keywords = [
        "earned",
        "received",
        "salary",
        "credited",
        "income",
    ]

    expense_keywords = [
        "spent",
        "spend",
        "paid",
        "bought",
        "purchase",
        "purchased",
        "cost",
    ]

    if any(keyword in message_lower for keyword in income_keywords):
        transaction_type = "income"
    else:
        transaction_type = "expense"

    description = message

    # Remove the amount
    description = re.sub(
        r"(?:₹|rs\.?|inr)?\s*\d+(?:\.\d+)?",
        "",
        description,
        flags=re.IGNORECASE,
    )

    # Remove transaction/action words
    action_words = expense_keywords + [
        "earned",
        "received",
        "credited",
    ]

    for keyword in action_words:
        description = re.sub(
            rf"\b{keyword}\b",
            "",
            description,
            flags=re.IGNORECASE,
        )

    # Remove conversational filler
    description = re.sub(
        r"\b(i|on|for|from|my|the)\b",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(r"\s+", " ", description).strip()

    return {
        "amount": amount,
        "description": description,
        "transaction_type": transaction_type,
    }