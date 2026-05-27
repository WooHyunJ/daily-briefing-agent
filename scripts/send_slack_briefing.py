import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.loop import DailyBriefingAgent
from app.services.formatting import format_briefing_text
from app.tools.slack import SlackNotifier


async def main() -> None:
    agent = DailyBriefingAgent()
    briefing = await agent.run()
    message = format_briefing_text(briefing)

    notifier = SlackNotifier()
    if not notifier.is_enabled():
        print(message)
        print("\nSlack 설정이 꺼져 있어 메시지를 전송하지 않았습니다.")
        return

    await notifier.send(message)
    print("Slack 브리핑을 전송했습니다.")


if __name__ == "__main__":
    asyncio.run(main())
