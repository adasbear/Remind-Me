from datetime import datetime, timezone, timedelta

# Addis Ababa is UTC+3
EAT = timezone(timedelta(hours=3))


def now_eat() -> datetime:
    return datetime.now(EAT)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def format_eat(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    eat_time = dt.astimezone(EAT)
    return eat_time.strftime("%I:%M %p").lstrip("0")


def format_eat_full(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    eat_time = dt.astimezone(EAT)
    return eat_time.strftime("%A, %B %d, %Y at %I:%M %p").lstrip("0")


def format_eat_short(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    eat_time = dt.astimezone(EAT)
    return eat_time.strftime("%b %d at %I:%M %p").lstrip("0")


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
    return dt.astimezone(timezone.utc)


def to_eat(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EAT)


def parse_iso_to_utc(iso_str: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
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
