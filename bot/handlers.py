import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from services.ai_service import extract_task
from services.timezone_helper import (
    format_eat_full,
    format_eat,
    parse_iso_to_eat,
    now_eat,
)
from database.task_repository import (
    upsert_user,
    save_task,
    get_user_active_tasks,
    mark_completed,
    mark_cancelled,
    find_task_by_title_partial,
)
from bot.keyboards import task_action_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    await update.message.reply_text(
        f"Hey {user.first_name}! I'm your task & reminder bot.\n\n"
        "How to use me:\n"
        "Just send me a message like:\n\n"
        '\u2022 Remind me to buy groceries tomorrow at 6 PM\n'
        '\u2022 Dentist appointment on Friday at 3 PM\n'
        '\u2022 Call mom in 30 minutes\n'
        '\u2022 Ping me 30 mins before my meeting\n\n'
        "I'll understand what you mean and set up the reminder.\n\n"
        "Commands:\n"
        "/list \u2014 see your active tasks\n"
        "/help \u2014 show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use me:\n\n"
        "Just type naturally, for example:\n"
        '\u2022 "Remind me to submit the report by Friday at 5 PM"\n'
        '\u2022 "Meeting with team tomorrow at 10 AM"\n'
        '\u2022 "Ping me 30 mins before my flight"\n\n'
        "Commands:\n"
        "/list - View your active tasks\n"
        "/help - Show this help"
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    tasks = get_user_active_tasks(telegram_id, limit=10)

    if not tasks:
        await update.message.reply_text("You have no active tasks. Tell me what you need to remember!")
        return

    lines = ["Your active tasks:\n"]
    for i, task in enumerate(tasks, 1):
        due = task.get("due_datetime", "")
        try:
            dt = datetime.fromisoformat(due)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            due_str = format_eat_full(dt)
        except (ValueError, TypeError):
            due_str = "No due date"

        status_emoji = "\u23f0" if task["status"] == "pending" else "\U0001f4e2"
        lines.append(f"{status_emoji} {i}. {task['title']}\n   Due: {due_str}")

    await update.message.reply_text("\n".join(lines))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if not text:
        return

    upsert_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    try:
        result = extract_task(text)
    except Exception as e:
        logger.error("AI extraction failed: %s", e)
        await update.message.reply_text(
            "Sorry, I couldn't understand that. Try something like:\n"
            '\u2022 "Remind me to buy milk tomorrow at 6 PM"'
        )
        return

    intent = result.intent

    if intent == "list_tasks":
        await _handle_list(update, user.id)
        return

    if intent == "complete_task":
        await _handle_complete(update, user.id, result)
        return

    if intent == "delete_task":
        await _handle_delete(update, user.id, result)
        return

    if intent == "create_task":
        await _handle_create(update, user.id, result)
        return

    # general_query or fallback
    await update.message.reply_text(result.conversational_reply)


async def _handle_create(update: Update, telegram_id: int, result):
    if not result.title or not result.due_datetime_iso:
        await update.message.reply_text(
            result.conversational_reply
            or "I couldn't figure out the task or time. Can you rephrase?"
        )
        return

    logger.info("AI returned: title=%s, due=%s, reminder=%s",
                result.title, result.due_datetime_iso, result.reminder_datetime_iso)

    # Parse Gemini's response into Addis Ababa time
    due_eat = parse_iso_to_eat(result.due_datetime_iso)

    if result.reminder_datetime_iso:
        reminder_eat = parse_iso_to_eat(result.reminder_datetime_iso)
    else:
        reminder_eat = None

    if due_eat is None:
        await update.message.reply_text("I couldn't understand the date/time. Please try again.")
        return

    # Default reminder: 15 mins before due
    if reminder_eat is None:
        reminder_eat = due_eat - timedelta(minutes=15)

    logger.info("Parsed EAT times: due=%s, reminder=%s", due_eat, reminder_eat)

    # Save to database (stores as device time)
    task = save_task(
        telegram_id=telegram_id,
        title=result.title,
        description=result.description,
        due_dt=due_eat,
        reminder_dt=reminder_eat,
    )

    due_str = format_eat_full(due_eat)
    reminder_str = format_eat(reminder_eat)

    await update.message.reply_text(
        f"\u2705 Task created!\n\n"
        f"\U0001f4cc {result.title}\n"
        f"\U0001f4c5 Due: {due_str} EAT\n"
        f"\u23f0 Reminder at: {reminder_str} EAT"
    )


async def _handle_list(update: Update, telegram_id: int):
    tasks = get_user_active_tasks(telegram_id, limit=10)
    if not tasks:
        await update.message.reply_text("You have no active tasks.")
        return

    lines = ["Your tasks:\n"]
    for i, task in enumerate(tasks, 1):
        due = task.get("due_datetime", "")
        try:
            dt = datetime.fromisoformat(due)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            due_str = format_eat_full(dt)
        except (ValueError, TypeError):
            due_str = "No due date"

        lines.append(f"{i}. {task['title']}\n   Due: {due_str} EAT")

    await update.message.reply_text("\n".join(lines))


async def _handle_complete(update: Update, telegram_id: int, result):
    query = result.target_task_id or result.title
    if not query:
        await update.message.reply_text("Which task did you complete? Tell me the task name.")
        return

    task = find_task_by_title_partial(telegram_id, query)
    if not task:
        await update.message.reply_text(f"No active task found matching '{query}'.")
        return

    mark_completed(task["id"])
    await update.message.reply_text(f"\u2705 Done! '{task['title']}' marked as completed.")


async def _handle_delete(update: Update, telegram_id: int, result):
    query = result.target_task_id or result.title
    if not query:
        await update.message.reply_text("Which task do you want to delete? Tell me the task name.")
        return

    task = find_task_by_title_partial(telegram_id, query)
    if not task:
        await update.message.reply_text(f"No active task found matching '{query}'.")
        return

    mark_cancelled(task["id"])
    await update.message.reply_text(f"\U0001f5d1 Deleted '{task['title']}'.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("Cancelled.")
        return

    action, task_id = data.split(":", 1)

    if action == "complete":
        mark_completed(task_id)
        await query.edit_message_text("\u2705 Task completed!")
    elif action == "delete":
        mark_cancelled(task_id)
        await query.edit_message_text("\U0001f5d1 Task deleted.")
