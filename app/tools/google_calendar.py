import asyncio
import json
import time as time_module
import urllib.parse
import webbrowser
from datetime import date, datetime, time, timedelta, timezone as datetime_timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.config import settings
from app.models.schemas import CalendarEvent


class GoogleCalendarTool:
    name = "get_google_calendar_events"
    description = "Google Calendar에서 지정한 날짜의 일정을 가져옵니다."

    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    events_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    def __init__(self, data_dir: Path) -> None:
        self.credentials_path = data_dir / "google_calendar_credentials.json"
        self.token_path = data_dir / "google_calendar_token.json"

    async def run(
        self,
        target_date: date,
        timezone: str,
        days: int = 1,
    ) -> list[CalendarEvent] | None:
        return await asyncio.to_thread(self._fetch_events, target_date, timezone, days)

    def _fetch_events(
        self,
        target_date: date,
        timezone: str,
        days: int,
    ) -> list[CalendarEvent] | None:
        if not settings.use_google_calendar:
            return None

        if not self.credentials_path.exists():
            return None

        try:
            access_token = self._get_access_token()
        except Exception:
            return None

        zone = self._get_timezone(timezone)
        window_days = max(days, 1)
        start_dt = datetime.combine(target_date, time.min, tzinfo=zone)
        end_dt = datetime.combine(
            target_date + timedelta(days=window_days - 1),
            time.max,
            tzinfo=zone,
        )

        params = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(self.events_url, params=params, headers=headers)
                response.raise_for_status()
                events_result = response.json()
        except httpx.HTTPError:
            return None

        events = []
        for item in events_result.get("items", []):
            start_value = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            end_value = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
            if not start_value or not end_value:
                continue

            events.append(
                CalendarEvent(
                    title=item.get("summary", "제목 없는 일정"),
                    start=self._parse_google_datetime(start_value, zone),
                    end=self._parse_google_datetime(end_value, zone),
                    location=item.get("location"),
                    attendees=[
                        attendee.get("email", "")
                        for attendee in item.get("attendees", [])
                        if attendee.get("email")
                    ],
                    notes=item.get("description"),
                )
            )

        return events

    def _get_access_token(self) -> str:
        credentials = self._load_client_credentials()
        token = self._load_token()

        if token and token.get("access_token") and not self._is_expired(token):
            return token["access_token"]

        if token and token.get("refresh_token"):
            refreshed_token = self._refresh_access_token(credentials, token["refresh_token"])
            token.update(refreshed_token)
            self._save_token(token)
            return token["access_token"]

        new_token = self._authorize(credentials)
        self._save_token(new_token)
        return new_token["access_token"]

    def _load_client_credentials(self) -> dict:
        data = json.loads(self.credentials_path.read_text(encoding="utf-8"))
        return data.get("installed") or data.get("web") or data

    def _load_token(self) -> dict | None:
        if not self.token_path.exists():
            return None

        return json.loads(self.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token: dict) -> None:
        if token.get("expires_in"):
            token["expires_at"] = int(time_module.time()) + int(token["expires_in"]) - 60

        self.token_path.write_text(
            json.dumps(token, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _is_expired(self, token: dict) -> bool:
        expires_at = int(token.get("expires_at", 0))
        return expires_at <= int(time_module.time())

    def _refresh_access_token(self, credentials: dict, refresh_token: str) -> dict:
        payload = {
            "client_id": credentials["client_id"],
            "client_secret": credentials.get("client_secret", ""),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        with httpx.Client(timeout=15) as client:
            response = client.post(self.token_url, data=payload)
            response.raise_for_status()
            return response.json()

    def _authorize(self, credentials: dict) -> dict:
        server = HTTPServer(("localhost", 0), _OAuthCallbackHandler)
        redirect_uri = f"http://localhost:{server.server_port}/"
        state = "daily-briefing-agent"

        params = {
            "client_id": credentials["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        webbrowser.open(auth_url)
        server.handle_request()

        code = getattr(server, "auth_code", None)
        returned_state = getattr(server, "auth_state", None)
        if not code or returned_state != state:
            raise RuntimeError("Google Calendar 인증 코드를 받지 못했습니다.")

        payload = {
            "client_id": credentials["client_id"],
            "client_secret": credentials.get("client_secret", ""),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        with httpx.Client(timeout=15) as client:
            response = client.post(self.token_url, data=payload)
            response.raise_for_status()
            return response.json()

    def _get_timezone(self, timezone: str):
        try:
            return ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            if timezone == "Asia/Seoul":
                return datetime_timezone(timedelta(hours=9), name="Asia/Seoul")

            return datetime_timezone.utc

    def _parse_google_datetime(self, value: str, zone) -> datetime:
        if "T" not in value:
            return datetime.combine(date.fromisoformat(value), time.min, tzinfo=zone)

        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_url.query)

        self.server.auth_code = query.get("code", [None])[0]
        self.server.auth_state = query.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "Google Calendar 인증이 완료되었습니다. 이 창을 닫고 앱으로 돌아가세요.".encode("utf-8")
        )

    def log_message(self, format: str, *args) -> None:
        return
