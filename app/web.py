import urllib.parse
from html import escape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.agent.loop import DailyBriefingAgent
from app.config import settings
from app.models.schemas import DailyBriefing, DailyCheckIn


app = FastAPI(title="Daily Briefing Agent")


def render_page(
    briefing: DailyBriefing | None = None,
    checkin: DailyCheckIn | None = None,
) -> HTMLResponse:
    checkin = checkin or DailyCheckIn(
        sleep_hours=6.5,
        energy_level=3,
        mood="보통",
        health_notes="",
        focus_capacity="오전 집중 가능, 오후 피로 예상",
    )

    briefing_html = ""
    if briefing:
        briefing_html = f"""
        <section class="briefing">
          <h2>{escape(briefing.headline)}</h2>
          <div class="briefing-grid">
            <div>
              {render_list("오늘의 우선순위", briefing.priorities)}
              {render_list("오늘 일정", briefing.today_schedule)}
              {render_list("다가오는 일정", briefing.upcoming_schedule)}
              {render_list("공지 메일", briefing.important_emails)}
            </div>
            <div>
              {render_list("일정 전략", briefing.schedule_strategy)}
              {render_list("에너지 운영", briefing.energy_strategy)}
              {render_list("날씨와 이동 준비", briefing.weather_and_commute)}
              {render_list("출근길 지하철", briefing.transit_updates)}
              {render_list("리스크 감지", briefing.risks)}
              {render_list("추천 행동", briefing.suggested_actions)}
            </div>
          </div>
        </section>
        """

    empty_state = (
        '<section class="panel empty">'
        "오늘 컨디션을 입력하고 브리핑을 생성하세요."
        "</section>"
    )

    html = f"""
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Daily Briefing Agent</title>
      <style>
        :root {{
          color-scheme: light;
          --bg: #f5f7fa;
          --panel: #ffffff;
          --text: #1f2937;
          --muted: #667085;
          --line: #d8dee8;
          --accent: #166534;
          --accent-strong: #14532d;
          --soft: #eef7f0;
          --warn: #9a3412;
          --warn-soft: #fff7ed;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif;
          background: var(--bg);
          color: var(--text);
        }}
        header {{
          border-bottom: 1px solid var(--line);
          background: var(--panel);
        }}
        .wrap {{
          width: min(1400px, calc(100% - 32px));
          margin: 0 auto;
        }}
        .topbar {{
          min-height: 72px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }}
        h1 {{
          margin: 0;
          font-size: 24px;
          letter-spacing: 0;
        }}
        .date {{
          color: var(--muted);
          font-size: 14px;
        }}
        main {{
          padding: 28px 0 40px;
        }}
        .layout {{
          display: grid;
          grid-template-columns: minmax(320px, 420px) 1fr;
          gap: 20px;
          align-items: start;
        }}
        .panel,
        .briefing {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 8px;
        }}
        .panel {{
          padding: 20px;
        }}
        .briefing {{
          padding: 24px 30px;
        }}
        .briefing-grid {{
          display: grid;
          grid-template-columns: minmax(260px, 0.9fr) minmax(320px, 1.1fr);
          gap: 28px;
        }}
        h2 {{
          margin: 0 0 18px;
          font-size: 22px;
          line-height: 1.35;
          letter-spacing: 0;
        }}
        h3 {{
          margin: 22px 0 10px;
          font-size: 16px;
          letter-spacing: 0;
        }}
        label {{
          display: block;
          margin: 14px 0 6px;
          font-weight: 650;
          font-size: 14px;
        }}
        input,
        textarea,
        select {{
          width: 100%;
          border: 1px solid var(--line);
          border-radius: 6px;
          padding: 10px 11px;
          font: inherit;
          background: #fff;
          color: var(--text);
        }}
        textarea {{
          min-height: 76px;
          resize: vertical;
        }}
        button {{
          width: 100%;
          margin-top: 18px;
          border: 0;
          border-radius: 6px;
          padding: 12px 14px;
          font: inherit;
          font-weight: 700;
          color: #fff;
          background: var(--accent);
          cursor: pointer;
        }}
        button:hover {{
          background: var(--accent-strong);
        }}
        .hint {{
          margin: 8px 0 0;
          color: var(--muted);
          font-size: 13px;
          line-height: 1.5;
        }}
        .status {{
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
          margin: 0 0 18px;
        }}
        .pill {{
          display: flex;
          justify-content: space-between;
          gap: 12px;
          border-radius: 6px;
          padding: 9px 10px;
          font-size: 13px;
          line-height: 1.35;
          background: var(--soft);
          color: var(--accent-strong);
        }}
        .pill.off {{
          background: var(--warn-soft);
          color: var(--warn);
        }}
        .pill strong {{
          font-weight: 750;
        }}
        .empty {{
          min-height: 360px;
          display: grid;
          place-items: center;
          color: var(--muted);
          text-align: center;
          padding: 28px;
        }}
        ul {{
          margin: 0;
          padding-left: 20px;
        }}
        li {{
          margin: 7px 0;
          line-height: 1.55;
        }}
        .briefing h3:first-of-type {{
          margin-top: 8px;
        }}
        @media (max-width: 1080px) {{
          .briefing-grid {{
            grid-template-columns: 1fr;
            gap: 4px;
          }}
        }}
        @media (max-width: 860px) {{
          .layout {{
            grid-template-columns: 1fr;
          }}
          .topbar {{
            align-items: flex-start;
            flex-direction: column;
            justify-content: center;
            padding: 16px 0;
          }}
        }}
      </style>
    </head>
    <body>
      <header>
        <div class="wrap topbar">
          <h1>Daily Briefing Agent</h1>
          <div class="date">컨디션 입력 기반 생활 브리핑</div>
        </div>
      </header>
      <main class="wrap">
        <div class="layout">
          <section class="panel">
            <h2>오늘 체크인</h2>
            {render_status_panel()}
            <form method="post" action="/briefing">
              <label for="sleep_hours">수면 시간</label>
              <input id="sleep_hours" name="sleep_hours" type="number" min="0" max="24" step="0.5" value="{escape(str(checkin.sleep_hours or ""))}">

              <label for="energy_level">에너지 수준</label>
              <select id="energy_level" name="energy_level">
                {render_energy_options(checkin.energy_level)}
              </select>

              <label for="mood">기분</label>
              <input id="mood" name="mood" value="{escape(checkin.mood or "")}" placeholder="예: 보통, 좋음, 조금 가라앉음">

              <label for="health_notes">건강 메모</label>
              <textarea id="health_notes" name="health_notes" placeholder="예: 목이 조금 칼칼함">{escape(checkin.health_notes or "")}</textarea>

              <label for="focus_capacity">집중 가능 시간</label>
              <textarea id="focus_capacity" name="focus_capacity" placeholder="예: 오전 집중 가능, 오후 피로 예상">{escape(checkin.focus_capacity or "")}</textarea>

              <button type="submit">브리핑 생성</button>
              <p class="hint">켜져 있는 연동은 실시간 데이터를 사용하고, 꺼진 연동은 로컬 기본값으로 대체합니다.</p>
            </form>
          </section>
          {briefing_html or empty_state}
        </div>
      </main>
    </body>
    </html>
    """
    return HTMLResponse(html)


def render_status_panel() -> str:
    items = [
        ("Google Calendar", settings.use_google_calendar),
        ("날씨 API", settings.use_weather_api and bool(settings.openweather_api_key)),
        ("Gmail", settings.use_gmail),
        ("지하철 API", settings.use_subway and bool(settings.seoul_subway_api_key)),
        ("Gemini", settings.use_gemini and bool(settings.gemini_api_key)),
        ("Slack", settings.use_slack and bool(settings.slack_webhook_url)),
    ]
    pills = []
    for label, enabled in items:
        state = "연결 사용" if enabled else "로컬/기본값"
        css_class = "pill" if enabled else "pill off"
        pills.append(
            f'<div class="{css_class}"><strong>{escape(label)}</strong><span>{escape(state)}</span></div>'
        )
    return f'<div class="status">{"".join(pills)}</div>'


def render_energy_options(selected: int | None) -> str:
    options = []
    for value in range(1, 6):
        label = f"{value} / 5"
        selected_attr = " selected" if selected == value else ""
        options.append(f'<option value="{value}"{selected_attr}>{label}</option>')
    return "".join(options)


def render_list(title: str, items: list[str]) -> str:
    if not items:
        return ""

    list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f"<h3>{escape(title)}</h3><ul>{list_items}</ul>"


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return render_page()


@app.post("/briefing", response_class=HTMLResponse)
async def create_briefing(request: Request) -> HTMLResponse:
    form = urllib.parse.parse_qs((await request.body()).decode("utf-8"))
    checkin = DailyCheckIn(
        sleep_hours=parse_float(form.get("sleep_hours", [""])[0]),
        energy_level=parse_int(form.get("energy_level", [""])[0]),
        mood=form.get("mood", [""])[0],
        health_notes=form.get("health_notes", [""])[0],
        focus_capacity=form.get("focus_capacity", [""])[0],
    )
    agent = DailyBriefingAgent()
    context = await agent.collect_context(daily_checkin=checkin)
    briefing = agent.briefing_service.generate(context)
    return render_page(briefing=briefing, checkin=checkin)


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
