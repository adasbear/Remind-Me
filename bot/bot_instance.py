from telegram.ext import ApplicationBuilder
from config.settings import settings


def create_bot_application() -> ApplicationBuilder:
    return ApplicationBuilder().token(settings.telegram_bot_token)
