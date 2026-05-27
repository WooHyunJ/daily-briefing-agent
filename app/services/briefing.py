import time
from datetime import date

from google import genai
from google.genai import types

from app.agent.prompts import BRIEFING_SYSTEM_PROMPT
from app.config import settings
from app.models.schemas import CalendarEvent, DailyBriefing, DailyContext


class BriefingService:
    def __init__(self) -> None:
        self.client = None
        if settings.use_gemini and settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, context: DailyContext) -> DailyBriefing:
        if self.client is None:
            return self._generate_fallback(context)

        last_error: Exception | None = None

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=(
                        "Create today's personalized briefing from this context:\n"
                        f"{context.model_dump_json(indent=2)}"
                    ),
                    config=types.GenerateContentConfig(
                        system_instruction=BRIEFING_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=DailyBriefing,
                    ),
                )
                return DailyBriefing.model_validate_json(response.text)
            except Exception as error:
                last_error = error
                if attempt < 2:
                    time.sleep(2)

        return self._generate_fallback(context, last_error)

    def _generate_fallback(
        self,
        context: DailyContext,
        error: Exception | None = None,
    ) -> DailyBriefing:
        current_date = date.fromisoformat(context.date)
        sorted_todos = sorted(context.todos, key=lambda item: item.priority)
        today_events = [event for event in context.calendar_events if event.start.date() == current_date]
        upcoming_events = [event for event in context.calendar_events if event.start.date() > current_date]

        priorities = [todo.title for todo in sorted_todos[:3]]
        today_schedule = [self._format_event(event) for event in today_events]
        upcoming_schedule = [self._format_event(event, include_date=True) for event in upcoming_events]
        schedule_strategy = self._build_schedule_strategy(today_events, upcoming_events)

        energy_strategy = []
        weather_and_commute = []
        risks = []
        suggested_actions = []

        if context.daily_checkin:
            if context.daily_checkin.sleep_hours is not None and context.daily_checkin.sleep_hours < 6:
                risks.append("수면 시간이 짧아 집중 작업을 오전 초반에 배치하는 편이 좋습니다.")
            if context.daily_checkin.energy_level is not None and context.daily_checkin.energy_level <= 2:
                energy_strategy.append("에너지가 낮으니 회의 준비와 짧은 처리 업무 위주로 하루를 작게 나누세요.")
            if context.daily_checkin.focus_capacity:
                energy_strategy.append(context.daily_checkin.focus_capacity)
            if context.daily_checkin.health_notes:
                energy_strategy.append(f"건강 메모를 고려하세요: {context.daily_checkin.health_notes}")

        if context.weather:
            weather_and_commute.append(
                f"현재 날씨는 {context.weather.summary}, 기온은 {context.weather.temperature_c}도입니다."
            )
            if "비" in context.weather.summary or "Rain" in context.weather.summary:
                weather_and_commute.append("우산과 이동 시간을 미리 챙기세요.")

        if context.commute_summary:
            weather_and_commute.append(context.commute_summary)

        if context.transit_updates:
            suggested_actions.append("출근 전 지하철 도착정보를 확인하세요.")

        if context.email_digest:
            suggested_actions.append("[공지] 메일이 있는지 먼저 확인하세요.")

        if sorted_todos:
            first_todo = sorted_todos[0]
            suggested_actions.append(f"가장 먼저 '{first_todo.title}'부터 시작하세요.")

        if upcoming_events:
            next_event = upcoming_events[0]
            suggested_actions.append(
                f"{next_event.start.strftime('%m/%d')} '{next_event.title}' 준비물을 오늘 미리 확인하세요."
            )

        if error:
            risks.append("AI 브리핑 서비스가 일시적으로 실패해 로컬 기본 브리핑으로 대체했습니다.")

        return DailyBriefing(
            headline="오늘은 일정과 컨디션을 함께 보며 우선순위를 좁히는 날입니다.",
            priorities=priorities or ["오늘 처리할 핵심 작업 하나를 먼저 정하세요."],
            today_schedule=today_schedule or ["오늘 등록된 일정이 없습니다."],
            upcoming_schedule=upcoming_schedule or ["다가오는 일정이 없습니다."],
            important_emails=context.email_digest or ["읽지 않은 [공지] 메일이 없습니다."],
            schedule_strategy=schedule_strategy,
            energy_strategy=energy_strategy or ["집중이 잘 되는 시간대에 가장 중요한 작업을 배치하세요."],
            weather_and_commute=weather_and_commute or ["외출 전 날씨와 이동 시간을 확인하세요."],
            transit_updates=context.transit_updates or ["실시간 지하철 도착정보가 설정되지 않았습니다."],
            risks=risks,
            suggested_actions=suggested_actions or ["작게 시작할 수 있는 첫 행동 하나를 정하고 바로 진행하세요."],
        )

    def _build_schedule_strategy(
        self,
        today_events: list[CalendarEvent],
        upcoming_events: list[CalendarEvent],
    ) -> list[str]:
        strategy = [
            (
                f"{event.start.strftime('%H:%M')} {event.title}: "
                f"시작 전 {event.prep_minutes or 15}분 준비 시간을 확보하세요."
            )
            for event in today_events
        ]

        strategy.extend(
            (
                f"{event.start.strftime('%m/%d %H:%M')} {event.title}: "
                "오늘은 필요한 자료와 이동 계획만 미리 확인하세요."
            )
            for event in upcoming_events[:3]
        )

        return strategy or ["일정 사이에 준비 시간과 이동 여유를 확보하세요."]

    def _format_event(self, event: CalendarEvent, include_date: bool = False) -> str:
        time_format = "%m/%d %H:%M" if include_date else "%H:%M"
        parts = [f"{event.start.strftime(time_format)} {event.title}"]
        if event.location:
            parts.append(f"장소: {event.location}")
        if event.notes:
            parts.append(event.notes)
        return " | ".join(parts)
