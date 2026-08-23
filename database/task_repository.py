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
    due_datetime: str,
    reminder_datetime: str,
) -> dict:
    db = get_supabase()
    result = db.table("tasks").insert({
        "telegram_id": telegram_id,
        "title": title,
        "description": description,
        "due_datetime": due_datetime,
        "reminder_datetime": reminder_datetime,
        "status": "pending",
    }).execute()
    return result.data[0] if result.data else {}


def get_pending_reminders() -> list[dict]:
    db = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()
    result = (
        db.table("tasks")
        .select("id, telegram_id, title, description, due_datetime, reminder_datetime")
        .eq("status", "pending")
        .lte("reminder_datetime", now_iso)
        .order("reminder_datetime")
        .execute()
    )
    return result.data or []


def mark_reminded(task_id: str):
    db = get_supabase()
    db.table("tasks").update({
        "status": "reminded",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", task_id).execute()


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
