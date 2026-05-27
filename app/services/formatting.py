from datetime import date

from app.models.schemas import DailyBriefing


def format_briefing_text(briefing: DailyBriefing) -> str:
    today = date.today().isoformat()
    sections = [
        ("오늘의 핵심", briefing.priorities),
        ("오늘 일정", briefing.today_schedule),
        ("다가오는 일정", briefing.upcoming_schedule),
        ("공지 메일", briefing.important_emails),
        ("일정 전략", briefing.schedule_strategy),
        ("에너지 운영", briefing.energy_strategy),
        ("날씨 / 이동", briefing.weather_and_commute),
        ("출근길 지하철", briefing.transit_updates),
        ("리스크", briefing.risks),
        ("추천 행동", briefing.suggested_actions),
    ]

    lines = [
        "*Daily Briefing Agent*",
        today,
        "",
        briefing.headline,
    ]

    for title, items in sections:
        if not items:
            continue
        lines.append("")
        lines.append(f"*{title}*")
        lines.extend(f"- {item}" for item in items)

    return "\n".join(lines)
