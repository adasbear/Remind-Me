import logging
from datetime import datetime, timezone
from typing import Optional
from database.client import get_supabase

logger = logging.getLogger(__name__)


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
    due_dt: datetime,
    reminder_dt: datetime,
) -> dict:
    """Save a task. Accepts timezone-aware datetimes."""
    db = get_supabase()

    # Ensure UTC for storage
    if due_dt.tzinfo:
        due_iso = due_dt.astimezone(timezone.utc).isoformat()
    else:
        due_iso = due_dt.isoformat()

    if reminder_dt.tzinfo:
        reminder_iso = reminder_dt.astimezone(timezone.utc).isoformat()
    else:
        reminder_iso = reminder_dt.isoformat()

    logger.info("Saving task: title=%s, due=%s, reminder=%s", title, due_iso, reminder_iso)

    result = db.table("tasks").insert({
        "telegram_id": telegram_id,
        "title": title,
        "description": description,
        "due_datetime": due_iso,
        "reminder_datetime": reminder_iso,
        "status": "pending",
    }).execute()
    return result.data[0] if result.data else {}


def mark_reminded(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "reminded",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", task_id).execute()
    logger.info("Marked task %s as reminded", task_id)


def mark_completed(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", task_id).execute()


def mark_cancelled(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "cancelled",
        "updated_at": datetime.now(timezone.utc).isoformat(),
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
