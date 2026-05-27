import asyncio

from app.agent.loop import DailyBriefingAgent


async def main() -> None:
    agent = DailyBriefingAgent()

    context = await agent.collect_context()
    if context.weather:
        print("====================================")
        print(f"날씨 요약: {context.weather.summary}")
        print(f"현재 기온: {context.weather.temperature_c}도")
        print("====================================\n")

    print("오늘 하루 브리핑을 생성하는 중입니다...\n")

    briefing = agent.briefing_service.generate(context)

    print(f"# {briefing.headline}\n")
    print("## 오늘의 우선순위")
    for item in briefing.priorities:
        print(f"- {item}")
    print("\n## 오늘 일정")
    for item in briefing.today_schedule:
        print(f"- {item}")
    print("\n## 다가오는 일정")
    for item in briefing.upcoming_schedule:
        print(f"- {item}")
    print("\n## 공지 메일")
    for item in briefing.important_emails:
        print(f"- {item}")
    print("\n## 일정 전략")
    for item in briefing.schedule_strategy:
        print(f"- {item}")
    print("\n## 에너지 운영")
    for item in briefing.energy_strategy:
        print(f"- {item}")
    print("\n## 날씨와 이동 준비")
    for item in briefing.weather_and_commute:
        print(f"- {item}")
    print("\n## 출근길 지하철")
    for item in briefing.transit_updates:
        print(f"- {item}")
    print("\n## 리스크 감지")
    for item in briefing.risks:
        print(f"- {item}")
    print("\n## 추천 행동")
    for item in briefing.suggested_actions:
        print(f"- {item}")


if __name__ == "__main__":
    asyncio.run(main())
