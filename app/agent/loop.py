import json
from datetime import date
from pathlib import Path

from app.config import settings
from app.models.schemas import (
    CalendarEvent,
    DailyBriefing,
    DailyCheckIn,
    DailyContext,
    TodoItem,
    UserProfile,
)
from app.services.briefing import BriefingService
from app.tools.gmail import GmailTool
from app.tools.google_calendar import GoogleCalendarTool
from app.tools.subway import SubwayArrivalTool
from app.tools.weather import WeatherTool


class DailyBriefingAgent:
    def __init__(self) -> None:
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.briefing_service = BriefingService()
        self.weather_tool = WeatherTool()
        self.google_calendar_tool = GoogleCalendarTool(self.data_dir)
        self.gmail_tool = GmailTool(self.data_dir)
        self.subway_tool = SubwayArrivalTool()

    def load_profile(self) -> UserProfile:
        profile_path = self.data_dir / "profile.json"
        if not profile_path.exists():
            return UserProfile()

        with profile_path.open("r", encoding="utf-8") as file:
            profile_data = json.load(file)

        return UserProfile.model_validate(profile_data)

    def load_todos(self) -> list[TodoItem]:
        todos_path = self.data_dir / "todos.json"
        if not todos_path.exists():
            return []

        with todos_path.open("r", encoding="utf-8") as file:
            todos_data = json.load(file)

        return [TodoItem.model_validate(item) for item in todos_data]

    def load_email_digest(self) -> list[str]:
        email_digest_path = self.data_dir / "email_digest.json"
        if not email_digest_path.exists():
            return []

        with email_digest_path.open("r", encoding="utf-8") as file:
            email_digest_data = json.load(file)

        return [str(item) for item in email_digest_data]

    def load_calendar_events(self) -> list[CalendarEvent]:
        calendar_events_path = self.data_dir / "calendar_events.json"
        if not calendar_events_path.exists():
            return []

        with calendar_events_path.open("r", encoding="utf-8") as file:
            calendar_events_data = json.load(file)

        return [CalendarEvent.model_validate(item) for item in calendar_events_data]

    def load_daily_checkin(self) -> DailyCheckIn | None:
        daily_checkin_path = self.data_dir / "daily_checkin.json"
        if not daily_checkin_path.exists():
            return None

        with daily_checkin_path.open("r", encoding="utf-8") as file:
            daily_checkin_data = json.load(file)

        return DailyCheckIn.model_validate(daily_checkin_data)

    async def collect_context(
        self,
        daily_checkin: DailyCheckIn | None = None,
    ) -> DailyContext:
        profile = self.load_profile()
        timezone = profile.timezone or settings.user_timezone
        today = date.today()

        weather = await self.weather_tool.run(city=profile.city)
        calendar_events = await self.google_calendar_tool.run(
            today,
            timezone,
            days=profile.calendar_window_days,
        )
        if calendar_events is None:
            calendar_events = self.load_calendar_events()
        email_digest = await self.gmail_tool.run()
        if email_digest is None:
            email_digest = self.load_email_digest()
        transit_updates = await self.subway_tool.run(profile)
        if transit_updates is None:
            transit_updates = []

        return DailyContext(
            date=today.isoformat(),
            timezone=timezone,
            user_profile=profile,
            daily_checkin=daily_checkin or self.load_daily_checkin(),
            calendar_events=calendar_events,
            weather=weather,
            todos=self.load_todos(),
            email_digest=email_digest,
            commute_summary=profile.commute_summary,
            transit_updates=transit_updates,
        )

    async def run(self) -> DailyBriefing:
        context = await self.collect_context()
        return self.briefing_service.generate(context)
