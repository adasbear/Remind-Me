import asyncio
import logging
from datetime import datetime, timezone

from database.task_repository import get_pending_reminders, mark_reminded

logger = logging.getLogger(__name__)

_bot_app = None
_poll_interval = 60  # seconds


def set_bot_app(bot_app):
    global _bot_app
    _bot_app = bot_app


async def _poll_and_send_reminders():
    while True:
        try:
            await _check_reminders()
        except Exception as e:
            logger.error("Reminder poller error: %s", e)
        await asyncio.sleep(_poll_interval)


async def _check_reminders():
    if _bot_app is None:
        return

    pending = get_pending_reminders()
    if not pending:
        return

    logger.info("Found %d due reminders", len(pending))

    for task in pending:
        telegram_id = task["telegram_id"]
        title = task["title"]
        due = task.get("due_datetime", "")

        # Convert due time to Addis Ababa for display
        try:
            due_dt = datetime.fromisoformat(due)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
            from services.timezone_helper import format_eat_full
            due_str = format_eat_full(due_dt)
        except (ValueError, TypeError):
            due_str = due

        text = (
            f"\u23f0 Task Reminder!\n\n"
            f"\U0001f4cc {title}\n"
            f"\U0001f4c5 Due: {due_str} EAT"
        )

        try:
            await _bot_app.bot.send_message(chat_id=telegram_id, text=text)
            mark_reminded(task["id"])
            logger.info("Sent reminder for task %s to %d", task["id"], telegram_id)
        except Exception as e:
            logger.error("Failed to send reminder to %d: %s", telegram_id, e)


async def start_scheduler():
    logger.info("Starting reminder scheduler (polling every %ds)", _poll_interval)
    asyncio.create_task(_poll_and_send_reminders())
