import logging
import uuid
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from database.task_repository import mark_reminded

logger = logging.getLogger(__name__)

# Addis Ababa = UTC+3
EAT = timezone(timedelta(hours=3))

scheduler = AsyncIOScheduler(timezone=timezone.utc)
_bot_app = None


def set_bot_app(bot_app):
    global _bot_app
    _bot_app = bot_app


def schedule_reminder(task_id: str, chat_id: int, title: str, due_display: str, run_at_utc: datetime):
    """Schedule a single reminder job at an exact UTC time."""
    job_id = f"reminder_{task_id}_{uuid.uuid4().hex[:8]}"

    def send_reminder():
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_send_message(chat_id, title, due_display, task_id, job_id))
        else:
            loop.run_until_complete(_send_message(chat_id, title, due_display, task_id, job_id))

    scheduler.add_job(
        func=send_reminder,
        trigger=DateTrigger(run_date=run_at_utc),
        id=job_id,
        replace_existing=True,
    )
    logger.info("Scheduled reminder: task=%s, job=%s, fire_at=%s UTC", task_id, job_id, run_at_utc)
    return job_id


async def _send_message(chat_id: int, title: str, due_display: str, task_id: str, job_id: str):
    if _bot_app is None:
        return

    text = (
        f"\u23f0 Task Reminder!\n\n"
        f"\U0001f4cc {title}\n"
        f"\U0001f4c5 Due: {due_display}"
    )

    try:
        await _bot_app.bot.send_message(chat_id=chat_id, text=text)
        mark_reminded(task_id)
        logger.info("Sent reminder for task %s to %d", task_id, chat_id)
    except Exception as e:
        logger.error("Failed to send reminder to %d: %s", chat_id, e)


def parse_eat_to_utc(eat_dt: datetime) -> datetime:
    """Convert an Addis Ababa datetime to UTC for APScheduler."""
    if eat_dt.tzinfo is None:
        eat_dt = eat_dt.replace(tzinfo=EAT)
    return eat_dt.astimezone(timezone.utc)


def start_scheduler():
    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
