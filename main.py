import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config.settings import settings
from bot.bot_instance import create_bot_application
from bot.handlers import start_command, help_command, list_command, handle_message, handle_callback
from services.scheduler_service import set_bot_app, start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TaskNova Bot")

bot_app: Application = None


@app.on_event("startup")
async def on_startup():
    global bot_app

    builder = create_bot_application()
    application = builder.build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    bot_app = application
    set_bot_app(application)

    # Set webhook - non-blocking, won't crash the app if it fails
    webhook_url = settings.telegram_webhook_url
    if webhook_url and "placeholder" not in webhook_url:
        try:
            await application.bot.set_webhook(url=webhook_url)
            logger.info("Webhook set to %s", webhook_url)
        except Exception as e:
            logger.warning("Failed to set webhook (you can set it manually): %s", e)
    else:
        logger.info("No webhook URL configured, skipping auto-set. Set it manually via Telegram API.")

    await start_scheduler()
    logger.info("TaskNova bot started")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=False)
