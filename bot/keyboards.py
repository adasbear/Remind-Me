from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def task_action_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2705 Done", callback_data=f"complete:{task_id}"),
            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"delete:{task_id}"),
        ]
    ])


def confirm_keyboard(action: str, task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes", callback_data=f"confirm_{action}:{task_id}"),
            InlineKeyboardButton("No", callback_data="cancel"),
        ]
    ])
