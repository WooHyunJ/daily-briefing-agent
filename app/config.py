import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    user_timezone: str = "Asia/Seoul"
    openweather_api_key: str | None = os.getenv("OPENWEATHER_API_KEY")
    use_gemini: bool = os.getenv("USE_GEMINI", "false").lower() == "true"
    use_weather_api: bool = os.getenv("USE_WEATHER_API", "false").lower() == "true"
    use_google_calendar: bool = os.getenv("USE_GOOGLE_CALENDAR", "false").lower() == "true"
    use_gmail: bool = os.getenv("USE_GMAIL", "false").lower() == "true"
    gmail_max_messages: int = int(os.getenv("GMAIL_MAX_MESSAGES", "10"))
    gmail_important_keywords: str = os.getenv(
        "GMAIL_IMPORTANT_KEYWORDS",
        "[공지]",
    )
    use_slack: bool = os.getenv("USE_SLACK", "false").lower() == "true"
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    use_subway: bool = os.getenv("USE_SUBWAY", "false").lower() == "true"
    seoul_subway_api_key: str = os.getenv("SEOUL_SUBWAY_API_KEY", "")
    subway_arrival_limit: int = int(os.getenv("SUBWAY_ARRIVAL_LIMIT", "5"))
    use_event_reminders: bool = os.getenv("USE_EVENT_REMINDERS", "false").lower() == "true"
    event_reminder_minutes: int = int(os.getenv("EVENT_REMINDER_MINUTES", "30"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
