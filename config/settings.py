import os
from dotenv import load_dotenv

load_dotenv()


class settings:
    telegram_bot_token: str = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_webhook_url: str = os.environ.get("TELEGRAM_WEBHOOK_URL", "")

    supabase_url: str = os.environ["SUPABASE_URL"]
    supabase_key: str = os.environ["SUPABASE_KEY"]

    gemini_api_key: str = os.environ["GEMINI_API_KEY"]

    default_timezone: str = os.environ.get("DEFAULT_TIMEZONE", "Africa/Addis_Ababa")
    port: int = int(os.environ.get("PORT", "8000"))
    environment: str = os.environ.get("ENVIRONMENT", "production")
