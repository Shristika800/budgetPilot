def generate_advice(summary: dict) -> str:
    income = summary["total_income"]
    expenses = summary["total_expenses"]
    categories = summary["spending_by_category"]

    advice = []

    if expenses == 0:
        return "You haven't recorded any expenses yet."

    if income == 0:
        advice.append(
            "You have recorded expenses but no income for this period."
        )

    elif expenses > income:
        advice.append(
            f"You're spending ₹{expenses - income:.2f} more "
            f"than your recorded income."
        )

    else:
        savings_rate = ((income - expenses) / income) * 100

        advice.append(
            f"You're currently saving about {savings_rate:.1f}% "
            f"of your recorded income."
        )

    if categories:
        top_category = categories[0]
        top_amount = top_category["amount"]

        percentage = (top_amount / expenses) * 100

        advice.append(
            f"Your biggest spending category is "
            f"{top_category['category']} at ₹{top_amount:.2f}, "
            f"which is {percentage:.1f}% of your spending."
        )

        if percentage >= 50:
            advice.append(
                f"More than half of your recorded spending is going "
                f"toward {top_category['category']}. "
                f"That may be the first category worth reviewing."
            )

    return " ".join(advice)