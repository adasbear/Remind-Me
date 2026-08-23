from datetime import datetime, timezone, timedelta

# Addis Ababa = UTC+3
EAT = timezone(timedelta(hours=3))


def now_eat() -> datetime:
    return datetime.now(EAT)


def format_eat(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def format_eat_full(dt: datetime) -> str:
    return dt.strftime("%A, %B %d, %Y at %I:%M %p").lstrip("0")


def parse_iso_to_eat(iso_str: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=EAT)
        return dt.astimezone(EAT)
    except (ValueError, TypeError):
        return None


def current_time_context() -> str:
    now = now_eat()
    hour = now.hour
    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 21:
        period = "evening"
    else:
        period = "night"
    return f"{now.strftime('%A')} {period}, {now.strftime('%I:%M %p').lstrip('0')} EAT"
