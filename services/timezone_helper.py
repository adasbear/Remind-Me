from datetime import datetime, timezone, timedelta

# Addis Ababa is UTC+3
EAT = timezone(timedelta(hours=3))
UTC = timezone.utc


def now_eat() -> datetime:
    return datetime.now(EAT)


def now_utc() -> datetime:
    return datetime.now(UTC)


def eat_to_utc(dt: datetime) -> datetime:
    """Convert an Addis Ababa datetime to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
    return dt.astimezone(UTC)


def utc_to_eat(dt: datetime) -> datetime:
    """Convert a UTC datetime to Addis Ababa time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(EAT)


def format_eat(dt: datetime) -> str:
    """Format a datetime as '3:45 PM' in Addis Ababa time."""
    eat = utc_to_eat(dt) if dt.tzinfo == UTC else dt.astimezone(EAT)
    return eat.strftime("%I:%M %p").lstrip("0")


def format_eat_full(dt: datetime) -> str:
    """Format a datetime as 'Monday, August 24, 2026 at 10:00 PM' in Addis Ababa time."""
    eat = utc_to_eat(dt) if dt.tzinfo == UTC else dt.astimezone(EAT)
    return eat.strftime("%A, %B %d, %Y at %I:%M %p").lstrip("0")


def parse_iso_to_eat(iso_str: str) -> datetime | None:
    """Parse any ISO 8601 string and return an Addis Ababa datetime."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            # No timezone info — assume it's already Addis Ababa time
            dt = dt.replace(tzinfo=EAT)
        return dt.astimezone(EAT)
    except (ValueError, TypeError):
        return None


def eat_now_iso() -> str:
    """Return current Addis Ababa time as ISO string for Supabase queries.
    Format: '2026-08-24T22:00:00+03:00'
    """
    return now_eat().isoformat()


def current_time_context() -> str:
    """Return a human-readable description of the current time."""
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
