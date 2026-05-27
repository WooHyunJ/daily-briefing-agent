from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str = "사용자"
    timezone: str = "Asia/Seoul"
    city: str = "Incheon"
    calendar_window_days: int = 3
    commute_summary: str | None = None
    commute_station: str | None = None
    commute_subway_line: str | None = None
    commute_direction_keyword: str | None = None
    wake_time: str | None = None
    sleep_time: str | None = None
    work_start: str | None = None
    work_end: str | None = None
    briefing_style: str = "concise"


class CalendarEvent(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: str | None = None
    attendees: list[str] = Field(default_factory=list)
    prep_minutes: int = 0
    travel_required: bool = False
    importance: int = 3
    notes: str | None = None


class WeatherSnapshot(BaseModel):
    summary: str
    temperature_c: float | None = None


class TodoItem(BaseModel):
    title: str
    due: datetime | None = None
    priority: int = 3
    source: str = "local"
    related_event: str | None = None
    estimated_minutes: int | None = None
    energy: str | None = None
    notes: str | None = None


class DailyCheckIn(BaseModel):
    sleep_hours: float | None = None
    energy_level: int | None = None
    mood: str | None = None
    health_notes: str | None = None
    focus_capacity: str | None = None


class DailyContext(BaseModel):
    date: str
    timezone: str
    user_profile: UserProfile | None = None
    daily_checkin: DailyCheckIn | None = None
    calendar_events: list[CalendarEvent] = Field(default_factory=list)
    todos: list[TodoItem] = Field(default_factory=list)
    weather: WeatherSnapshot | None = None
    commute_summary: str | None = None
    transit_updates: list[str] = Field(default_factory=list)
    email_digest: list[str] = Field(default_factory=list)


class DailyBriefing(BaseModel):
    headline: str
    priorities: list[str] = Field(default_factory=list)
    today_schedule: list[str] = Field(default_factory=list)
    upcoming_schedule: list[str] = Field(default_factory=list)
    important_emails: list[str] = Field(default_factory=list)
    schedule_strategy: list[str] = Field(default_factory=list)
    energy_strategy: list[str] = Field(default_factory=list)
    weather_and_commute: list[str] = Field(default_factory=list)
    transit_updates: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
