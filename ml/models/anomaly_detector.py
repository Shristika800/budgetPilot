import statistics

# Flag a transaction if its amount is more than Z_THRESHOLD standard deviations
# above the category mean. Requires at least MIN_SAMPLES past transactions.
Z_THRESHOLD = 2.0
MIN_SAMPLES = 5


def detect_anomaly(
    amount: float,
    category: str,
    historical_amounts: list[float],
) -> dict:
    if len(historical_amounts) < MIN_SAMPLES:
        return {"is_anomaly": False, "reason": None, "z_score": None, "mean": None}

    mean = statistics.mean(historical_amounts)
    stdev = statistics.stdev(historical_amounts)

    if stdev == 0:
        is_anomaly = amount > mean * 2
        return {
            "is_anomaly": is_anomaly,
            "reason": (
                f"This {category} transaction (₹{amount:.2f}) is more than "
                f"double your usual amount (₹{mean:.2f})."
            ) if is_anomaly else None,
            "z_score": None,
            "mean": round(mean, 2),
        }

    z_score = (amount - mean) / stdev
    is_anomaly = z_score > Z_THRESHOLD

    return {
        "is_anomaly": is_anomaly,
        "reason": (
            f"This {category} transaction (₹{amount:.2f}) is unusually high. "
            f"Your average {category} spend is ₹{mean:.2f} — "
            f"this is {z_score:.1f}x the usual variation."
        ) if is_anomaly else None,
        "z_score": round(z_score, 2),
        "mean": round(mean, 2),
    }
