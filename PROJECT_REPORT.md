# Daily Briefing Agent 프로젝트 결과 보고서

## 1. 프로젝트명

Daily Briefing Agent

## 2. 프로젝트 목적

본 프로젝트는 사용자의 아침 준비 시간을 줄이고, 하루의 일정과 생활 정보를 한 번에 확인할 수 있도록 돕는 개인 생활지원 에이전트 구현을 목표로 한다.

기존에는 캘린더, 메일, 날씨, 교통, 할 일을 각각 확인해야 했다. 이 프로젝트는 여러 정보를 자동으로 수집하고 Slack 브리핑 형태로 전달하여 사용자가 하루의 우선순위와 준비사항을 빠르게 파악할 수 있게 한다.

## 3. 핵심 기능

### 3.1 웹 기반 오늘 체크인

FastAPI 기반 웹 화면에서 다음 정보를 입력할 수 있다.

- 수면 시간
- 에너지 수준
- 기분
- 건강 메모
- 집중 가능 시간

입력값은 당일 브리핑 생성에 반영된다.

### 3.2 Google Calendar 일정 브리핑

Google Calendar API를 통해 사용자의 일정을 조회한다.

- 오늘 일정
- 다가오는 일정
- 일정별 준비 시간
- 장소 및 메모

브리핑에서는 오늘 일정과 다가오는 일정을 분리하여 표시한다.

### 3.3 Gmail 공지 메일 감지

Gmail API를 통해 읽지 않은 메일 중 `[공지]` 키워드가 포함된 메일을 감지한다.

초기에는 중요 메일 3줄 요약 기능을 고려했으나, 개인정보 노출과 과도한 요약 자동화를 줄이기 위해 현재는 `[공지]` 메일 존재 여부와 제목/보낸 사람 중심의 알림으로 단순화했다.

### 3.4 날씨 정보 조회

OpenWeather API를 통해 현재 날씨와 기온을 조회한다.

API 키가 없거나 호출에 실패할 경우 기본 날씨 메시지로 대체된다.

### 3.5 지하철 실시간 도착정보

서울 열린데이터광장 실시간 지하철 도착정보 API를 사용해 출근역 기준 도착정보를 조회한다.

현재 설정:

- 출근역: 구로
- 호선: 1호선
- 방면 키워드: 용산, 소요산, 동두천

지연 알림 기능은 제외하고, 실시간 도착정보만 브리핑에 포함한다.

### 3.6 Slack 자동 브리핑

Slack Incoming Webhook을 통해 브리핑을 Slack 채널로 전송한다.

Windows 작업 스케줄러를 사용하여 매일 오전 7시 30분 자동 발송되도록 구성했다.

### 3.7 일정 전 Slack 리마인더

별도 스케줄러 작업을 통해 5분마다 Google Calendar를 확인한다.

앞으로 30분 안에 시작하는 일정이 있으면 Slack으로 리마인더를 전송한다. 같은 일정에 대해 하루에 한 번만 발송되도록 상태 파일을 사용한다.

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
- 서울 열린데이터광장 지하철 실시간 도착정보 API
- Slack Incoming Webhook
- Windows 작업 스케줄러

## 6. 구현 결과

구현된 결과는 다음과 같다.

- 웹에서 오늘 체크인 입력 가능
- 로컬/외부 API 데이터를 통합한 브리핑 생성 가능
- Slack 채널로 브리핑 수동 발송 가능
- 매일 오전 7시 30분 Slack 자동 발송 작업 등록 가능
- 일정 시작 전 Slack 리마인더 작업 등록 가능
- 민감정보가 GitHub에 올라가지 않도록 `.gitignore` 구성
- `.env.example`을 통해 설치자가 필요한 환경변수 확인 가능

## 7. 보안 및 개인정보 고려

다음 파일은 GitHub 업로드 대상에서 제외했다.

```text
.env
data/google_calendar_credentials.json
data/google_calendar_token.json
data/gmail_token.json
data/event_reminder_state.json
```

API 키, OAuth 토큰, Slack Webhook URL은 `.env` 또는 로컬 데이터 파일에만 저장한다.

## 8. 한계점

- Google Calendar는 현재 기본 캘린더 중심으로 조회한다.
- Gmail은 `[공지]` 키워드 감지만 수행하며 본문 요약은 제외했다.
- Slack은 메시지 수신 중심이며 대화형 명령은 구현하지 않았다.
- Windows 작업 스케줄러 기반이므로 PC가 꺼져 있으면 자동 발송되지 않는다.
- 지하철 API는 서울 열린데이터광장 인증키와 호출 제한에 영향을 받는다.

## 9. 향후 개선 방향

- 웹 설정 화면 추가
- 체크인 기록 저장
- 최근 브리핑 히스토리 조회
- Slack Block Kit 기반 메시지 디자인 개선
- Google Calendar 다중 캘린더 조회
- 작업 스케줄러 상태를 웹 화면에서 확인
- 일정 사이 빈 시간 분석 및 시간 블록 추천

## 10. 결론

Daily Briefing Agent는 개인의 일정, 날씨, 메일, 교통, 할 일을 통합해 Slack으로 전달하는 생활지원형 자동화 에이전트이다.

단순한 일정 요약을 넘어, 아침 브리핑과 일정 전 리마인더를 통해 사용자의 하루 준비와 실행을 돕는 구조를 구현했다. 또한 외부 API 실패 시 로컬 기본값으로 대체하는 fallback 구조를 적용해 안정성을 확보했다.
