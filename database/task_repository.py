import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from database.client import get_supabase

logger = logging.getLogger(__name__)

EAT = timezone(timedelta(hours=3))


def _to_utc_iso(dt_or_str) -> str:
    """Convert any datetime/ISO string to a clean UTC ISO string for storage."""
    if isinstance(dt_or_str, str):
        dt = datetime.fromisoformat(dt_or_str)
    else:
        dt = dt_or_str
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def upsert_user(telegram_id: int, first_name: str, username: Optional[str] = None):
    db = get_supabase()
    db.table("users").upsert({
        "telegram_id": telegram_id,
        "first_name": first_name,
        "username": username,
    }, on_conflict="telegram_id").execute()


def get_user(telegram_id: int) -> Optional[dict]:
    db = get_supabase()
    result = db.table("users").select("*").eq("telegram_id", telegram_id).limit(1).execute()
    return result.data[0] if result.data else None


def save_task(
    telegram_id: int,
    title: str,
    description: Optional[str],
    due_datetime: str,
    reminder_datetime: str,
) -> dict:
    db = get_supabase()
    due_utc = _to_utc_iso(due_datetime)
    reminder_utc = _to_utc_iso(reminder_datetime)

    logger.info("Saving task: title=%s, due=%s, reminder=%s", title, due_utc, reminder_utc)

    result = db.table("tasks").insert({
        "telegram_id": telegram_id,
        "title": title,
        "description": description,
        "due_datetime": due_utc,
        "reminder_datetime": reminder_utc,
        "status": "pending",
    }).execute()
    return result.data[0] if result.data else {}


def get_pending_reminders() -> list[dict]:
    db = get_supabase()
    now_iso = _now_utc_iso()

    logger.info("Querying pending reminders where reminder_datetime <= %s", now_iso)

    result = (
        db.table("tasks")
        .select("id, telegram_id, title, description, due_datetime, reminder_datetime")
        .eq("status", "pending")
        .lte("reminder_datetime", now_iso)
        .order("reminder_datetime")
        .execute()
    )
    reminders = result.data or []

    if reminders:
        for r in reminders:
            logger.info(
                "Due reminder: id=%s, title=%s, reminder_datetime=%s",
                r["id"], r["title"], r["reminder_datetime"]
            )

    return reminders


def mark_reminded(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "reminded",
        "updated_at": _now_utc_iso(),
    }).eq("id", task_id).execute()
    logger.info("Marked task %s as reminded", task_id)


def mark_completed(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "completed",
        "updated_at": _now_utc_iso(),
    }).eq("id", task_id).execute()


def mark_cancelled(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "cancelled",
        "updated_at": _now_utc_iso(),
    }).eq("id", task_id).execute()


def get_user_active_tasks(telegram_id: int, limit: int = 10) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("tasks")
        .select("id, title, description, due_datetime, status, created_at")
        .eq("telegram_id", telegram_id)
        .in_("status", ["pending", "reminded"])
        .order("due_datetime")
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_task_by_id(task_id: str) -> Optional[dict]:
    db = get_supabase()
    result = db.table("tasks").select("*").eq("id", task_id).limit(1).execute()
    return result.data[0] if result.data else None


def find_task_by_title_partial(telegram_id: int, title_query: str) -> Optional[dict]:
    db = get_supabase()
    result = (
        db.table("tasks")
        .select("id, title, due_datetime, status")
        .eq("telegram_id", telegram_id)
        .in_("status", ["pending", "reminded"])
        .ilike("title", f"%{title_query}%")
        .order("created_at")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
