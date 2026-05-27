import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.loop import DailyBriefingAgent
from app.config import settings
from app.tools.slack import SlackNotifier


def reminder_key(event_start: datetime, title: str) -> str:
    return f"{event_start.isoformat()}|{title}"


def load_sent_keys(path: Path, today: date) -> set[str]:
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()

    if data.get("date") != today.isoformat():
        return set()

    return set(data.get("sent", []))


def save_sent_keys(path: Path, today: date, sent: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"date": today.isoformat(), "sent": sorted(sent)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def to_local_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone(timedelta(hours=9), name="Asia/Seoul"))
    return value


def format_reminder(event, minutes_until: int) -> str:
    lines = [
        "*일정 리마인더*",
        f"{event.start.strftime('%H:%M')} '{event.title}' 일정이 약 {minutes_until}분 뒤 시작합니다.",
    ]
    if event.location:
        lines.append(f"장소: {event.location}")
    if event.notes:
        lines.append(f"확인할 내용: {event.notes}")
    if event.prep_minutes:
        lines.append(f"권장 준비 시간: {event.prep_minutes}분")
    return "\n".join(lines)


async def main() -> None:
    if not settings.use_event_reminders:
        print("일정 리마인더가 꺼져 있습니다.")
        return

    notifier = SlackNotifier()
    if not notifier.is_enabled():
        print("Slack 설정이 꺼져 있어 리마인더를 전송하지 않았습니다.")
        return

    agent = DailyBriefingAgent()
    context = await agent.collect_context()
    now = datetime.now(timezone(timedelta(hours=9), name="Asia/Seoul"))
    window_end = now + timedelta(minutes=max(settings.event_reminder_minutes, 1))
    state_path = agent.data_dir / "event_reminder_state.json"
    sent = load_sent_keys(state_path, now.date())
    sent_any = False

    for event in context.calendar_events:
        event_start = to_local_aware(event.start)
        if not now <= event_start <= window_end:
            continue

        key = reminder_key(event_start, event.title)
        if key in sent:
            continue

        minutes_until = max(0, round((event_start - now).total_seconds() / 60))
        await notifier.send(format_reminder(event, minutes_until))
        sent.add(key)
        sent_any = True
        print(f"리마인더 전송: {event.title}")

    save_sent_keys(state_path, now.date(), sent)
    if not sent_any:
        print("전송할 일정 리마인더가 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())
