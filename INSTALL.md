# Daily Briefing Agent 설치 가이드

## 1. 프로젝트 개요

Daily Briefing Agent는 일정, 날씨, Gmail 공지 메일, 지하철 도착정보, 할 일을 모아 매일 아침 Slack으로 브리핑을 보내는 생활지원 에이전트입니다.

주요 기능:

- 웹 기반 오늘 체크인 입력
- Google Calendar 일정 조회
- OpenWeather 현재 날씨 조회
- Gmail 읽지 않은 `[공지]` 메일 감지
- 서울 지하철 실시간 도착정보 조회
- Slack 아침 브리핑 자동 발송
- 일정 시작 전 Slack 리마인더

## 2. 요구 사항

- Windows 10 이상
- Python 3.13 또는 호환 버전
- Git
- Slack 워크스페이스 및 Incoming Webhook URL
- 선택 연동용 API 키
  - Google Calendar OAuth credentials
  - Gmail OAuth credentials
  - OpenWeather API key
  - 서울 열린데이터광장 실시간 지하철 인증키
  - Gemini API key

## 3. 설치

프로젝트 폴더로 이동합니다.

```powershell
cd "C:\Users\Administrator\Desktop\코덱스\daily-briefing-agent"
```

가상환경을 생성합니다.

```powershell
python -m venv .venv
```

패키지를 설치합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. 환경 변수 설정

`.env.example`을 복사해 `.env`를 만듭니다.

```powershell
Copy-Item .env.example .env
```

`.env` 파일에서 필요한 기능을 켭니다.

```env
GEMINI_API_KEY=
USER_TIMEZONE=Asia/Seoul
OPENWEATHER_API_KEY=
USE_GOOGLE_CALENDAR=true
USE_WEATHER_API=true
USE_GMAIL=true
GMAIL_MAX_MESSAGES=10
GMAIL_IMPORTANT_KEYWORDS=[공지]
USE_SLACK=true
SLACK_WEBHOOK_URL=
USE_SUBWAY=true
SEOUL_SUBWAY_API_KEY=
SUBWAY_ARRIVAL_LIMIT=5
USE_EVENT_REMINDERS=true
EVENT_REMINDER_MINUTES=30
```

주의: `.env`에는 실제 API 키와 Slack Webhook URL이 들어가므로 GitHub에 업로드하지 않습니다.

## 5. 사용자 프로필 설정

`data/profile.json`에서 사용자 정보와 출근 정보를 설정합니다.

```json
{
  "timezone": "Asia/Seoul",
  "city": "Incheon",
  "calendar_window_days": 3,
  "commute_summary": "출근길은 지하철 1호선 구로역 이용",
  "commute_station": "구로",
  "commute_subway_line": "1호선",
  "commute_direction_keyword": "용산,소요산,동두천"
}
```

## 6. 웹 앱 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.web:app --host 127.0.0.1 --port 8000
```

브라우저에서 접속합니다.

```text
http://127.0.0.1:8000/
```

## 7. Slack 브리핑 수동 테스트

```powershell
.\.venv\Scripts\python.exe scripts\send_slack_briefing.py
```

성공하면 Slack 채널에 브리핑이 전송됩니다.

## 8. 매일 오전 7시 30분 자동 발송 등록

관리자 권한 PowerShell에서 실행합니다.

```powershell
cd "C:\Users\Administrator\Desktop\코덱스\daily-briefing-agent"
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_slack_task.ps1
```

등록 확인:

```powershell
Get-ScheduledTask -TaskName "Daily Briefing Slack"
Get-ScheduledTaskInfo -TaskName "Daily Briefing Slack"
```

## 9. 일정 전 리마인더 등록

관리자 권한 PowerShell에서 실행합니다.

```powershell
cd "C:\Users\Administrator\Desktop\코덱스\daily-briefing-agent"
powershell -ExecutionPolicy Bypass -File .\scripts\register_event_reminder_task.ps1
```

이 작업은 5분마다 실행되며, 앞으로 30분 안에 시작하는 Google Calendar 일정이 있으면 Slack으로 리마인더를 보냅니다.

## 10. 주요 실행 명령

콘솔 브리핑:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Slack 브리핑:

```powershell
.\.venv\Scripts\python.exe scripts\send_slack_briefing.py
```

일정 리마인더:

```powershell
.\.venv\Scripts\python.exe scripts\send_event_reminders.py
```
