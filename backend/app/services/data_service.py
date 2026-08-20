from datetime import datetime, timedelta


def get_date_range(period: str):
    now = datetime.utcnow()

    if period == "today":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
        return start, end

    if period == "this_month":
        start = datetime(now.year, now.month, 1)

        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)

        return start, end

    if period == "last_month":
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1)
        else:
            start = datetime(now.year, now.month - 1, 1)

        end = datetime(now.year, now.month, 1)

        return start, end

    return None, None


def detect_period(message: str) -> str:
    message = message.lower()

    if "today" in message:
        return "today"

    if "last month" in message:
        return "last_month"

    if "this month" in message:
        return "this_month"

    return "this_month"