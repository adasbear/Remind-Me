import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from database.client import get_supabase
from services.timezone_helper import now_eat, EAT

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
    db = get_supabase()

    due_iso = due_dt.isoformat() if due_dt.tzinfo else due_dt.replace(tzinfo=EAT).isoformat()
    reminder_iso = reminder_dt.isoformat() if reminder_dt.tzinfo else reminder_dt.replace(tzinfo=EAT).isoformat()

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


def get_pending_reminders() -> list[dict]:
    db = get_supabase()
    now_iso = now_eat().isoformat()
    logger.info("Querying reminders where reminder_datetime <= %s", now_iso)

    result = (
        db.table("tasks")
        .select("id, telegram_id, title, description, due_datetime, reminder_datetime")
        .eq("status", "pending")
        .lte("reminder_datetime", now_iso)
        .order("reminder_datetime")
        .execute()
    )
    reminders = result.data or []

    for r in reminders:
        logger.info("Due task: id=%s, title=%s, reminder=%s", r["id"], r["title"], r["reminder_datetime"])

    return reminders


def mark_reminded(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "reminded",
        "updated_at": now_eat().isoformat(),
    }).eq("id", task_id).execute()
    logger.info("Marked task %s as reminded", task_id)


def mark_completed(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "completed",
        "updated_at": now_eat().isoformat(),
    }).eq("id", task_id).execute()


def mark_cancelled(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "cancelled",
        "updated_at": now_eat().isoformat(),
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
