# Daily Briefing Agent 프로젝트 결과 보고서

## 1. 프로젝트명

Daily Briefing Agent

## 2. 프로젝트 목적

이 프로젝트는 사용자의 아침 준비 시간을 줄이고, 하루 일정과 생활 정보를 한 번에 확인할 수 있도록 돕는 개인 생활 지원 에이전트입니다.

기존에는 캘린더, 메일, 날씨, 교통, 할 일을 각각 확인해야 했습니다. Daily Briefing Agent는 여러 정보를 자동으로 수집하고 Slack 브리핑 형태로 전달해 사용자가 하루의 우선순위와 준비 사항을 빠르게 파악할 수 있게 합니다.

## 3. 구현 기능

### 3.1 체크인 기반 브리핑

FastAPI 기반 웹 화면에서 다음 정보를 입력할 수 있습니다.

- 수면 시간
- 에너지 수준
- 기분
- 건강 메모
- 집중 가능 시간

입력값은 당일 브리핑 생성에 반영됩니다.

### 3.2 Google Calendar 일정 브리핑

Google Calendar API를 통해 사용자의 일정을 조회합니다.

- 오늘 일정
- 다가오는 일정
- 일정별 준비 시간
- 장소 및 메모

브리핑에서는 오늘 일정과 다가오는 일정을 분리해 표시합니다.

### 3.3 Gmail 중요 메일 감지

Gmail API를 통해 읽지 않은 메일 중 지정 키워드가 포함된 메일을 감지합니다. 기본 키워드는 `[공지]`입니다.

현재는 개인정보 노출과 과도한 자동 요약을 줄이기 위해 본문 요약 대신 제목과 보낸 사람 중심으로 알려줍니다.

### 3.4 날씨 정보 조회

OpenWeather API를 통해 현재 날씨와 기온을 조회합니다. API 키가 없거나 호출에 실패하면 기본 날씨 메시지로 대체합니다.

### 3.5 지하철 실시간 도착 정보

서울 열린데이터광장 지하철 API를 사용해 출근역 기준 도착 정보를 조회합니다.

현재 설정 예시:

- 출근역: 구로
- 노선: 1호선
- 방향 키워드: 용산, 청량리, 동두천

### 3.6 Slack 자동 브리핑

Slack Incoming Webhook을 통해 브리핑을 Slack 채널로 전송합니다. Windows 작업 스케줄러를 사용해 매일 오전 7시 30분 자동 발송할 수 있습니다.

### 3.7 일정 전 Slack 리마인더

별도 작업 스케줄러 작업을 통해 5분마다 Google Calendar를 확인합니다. 설정한 시간 안에 시작하는 일정이 있으면 Slack으로 리마인더를 보내며, 같은 일정은 하루에 한 번만 전송하도록 상태 파일을 사용합니다.

## 4. 시스템 구조

```text
daily-briefing-agent
├─ app
│  ├─ agent
│  │  ├─ loop.py
│  │  └─ prompts.py
│  ├─ models
│  │  └─ schemas.py
│  ├─ services
│  │  ├─ briefing.py
│  │  └─ formatting.py
│  ├─ tools
│  │  ├─ gmail.py
│  │  ├─ google_calendar.py
│  │  ├─ slack.py
│  │  ├─ subway.py
│  │  └─ weather.py
│  ├─ main.py
│  └─ web.py
├─ data
│  ├─ profile.json
│  ├─ todos.json
│  ├─ calendar_events.json
│  ├─ daily_checkin.json
│  └─ email_digest.json
├─ scripts
│  ├─ send_slack_briefing.py
│  ├─ send_event_reminders.py
│  ├─ register_daily_slack_task.ps1
│  └─ register_event_reminder_task.ps1
├─ requirements.txt
├─ .env.example
└─ .gitignore
```

## 5. 사용 기술

- Python
- FastAPI
- Pydantic
- httpx
- Google Calendar API
- Gmail API
- OpenWeather API
- 서울 열린데이터광장 지하철 API
- Slack Incoming Webhook
- Windows 작업 스케줄러
- Gemini API

## 6. 보안 및 개인정보 고려

다음 파일은 Git에 올리지 않도록 제외되어 있습니다.

```text
.env
data/google_calendar_credentials.json
data/google_calendar_token.json
data/gmail_token.json
data/event_reminder_state.json
```

API 키, OAuth 토큰, Slack Webhook URL은 로컬 파일에만 저장합니다.

## 7. 한계

- Google Calendar는 현재 기본 캘린더 중심으로 조회합니다.
- Gmail은 지정 키워드 감지만 수행하며 본문 요약은 제외했습니다.
- Slack은 메시지 수신 중심이며 대화형 명령은 구현하지 않았습니다.
- Windows 작업 스케줄러 기반이므로 PC가 꺼져 있으면 자동 발송되지 않습니다.
- 지하철 API는 서울 열린데이터광장 호출 제한의 영향을 받을 수 있습니다.

## 8. 향후 개선 방향

- 설정 관리 화면 추가
- 체크인 기록 저장
- 최근 브리핑 히스토리 조회
- Slack Block Kit 기반 메시지 디자인 개선
- Google Calendar 다중 캘린더 조회
- 작업 스케줄러 상태를 웹 화면에서 확인
- 일정 사이 빈 시간 분석 및 시간 블록 추천

## 9. 결론

Daily Briefing Agent는 일정, 날씨, 메일, 교통, 할 일을 통합해 Slack으로 전달하는 생활 지원형 자동화 에이전트입니다. 아침 브리핑과 일정 전 리마인더를 통해 사용자가 하루 준비와 실행을 더 빠르게 시작할 수 있도록 설계되었습니다.
