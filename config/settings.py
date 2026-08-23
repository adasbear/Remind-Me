from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: str = Field(..., env="TELEGRAM_WEBHOOK_URL")

    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")

    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    default_timezone: str = Field(default="Africa/Addis_Ababa", env="DEFAULT_TIMEZONE")
    port: int = Field(default=8000, env="PORT")
    environment: str = Field(default="production", env="ENVIRONMENT")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
