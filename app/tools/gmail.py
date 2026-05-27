import asyncio
import json
import re
import time as time_module
import urllib.parse
import webbrowser
from email.header import decode_header
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

from app.config import settings


class GmailTool:
    name = "get_unread_notice_email_alerts"
    description = "Gmail에서 읽지 않은 메일 중 지정 키워드가 있는 메일을 감지합니다."

    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    messages_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    def __init__(self, data_dir: Path) -> None:
        self.credentials_path = data_dir / "google_calendar_credentials.json"
        self.token_path = data_dir / "gmail_token.json"

    async def run(self) -> list[str] | None:
        if not settings.use_gmail:
            return None

        return await asyncio.to_thread(self._fetch_alerts)

    def _fetch_alerts(self) -> list[str] | None:
        if not self.credentials_path.exists():
            return None

        try:
            access_token = self._get_access_token()
            messages = self._list_notice_messages(access_token)
            return self._build_alerts(access_token, messages)
        except Exception:
            return None

    def _list_notice_messages(self, access_token: str) -> list[dict]:
        keywords = self._keywords()
        keyword_query = " OR ".join(f'"{keyword}"' for keyword in keywords)
        query = "is:unread newer_than:7d"
        if keyword_query:
            query = f"{query} ({keyword_query})"

        params = {
            "q": query,
            "maxResults": settings.gmail_max_messages,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client(timeout=20) as client:
            response = client.get(self.messages_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("messages", [])

    def _build_alerts(self, access_token: str, messages: list[dict]) -> list[str]:
        if not messages:
            return ["읽지 않은 중요 메일이 없습니다."]

        headers = {"Authorization": f"Bearer {access_token}"}
        alerts = [f"읽지 않은 중요 메일이 {len(messages)}건 있습니다."]

        with httpx.Client(timeout=20) as client:
            for message in messages[: settings.gmail_max_messages]:
                message_id = message.get("id")
                if not message_id:
                    continue

                response = client.get(
                    f"{self.messages_url}/{message_id}",
                    params={"format": "metadata", "metadataHeaders": ["From", "Subject"]},
                    headers=headers,
                )
                response.raise_for_status()
                detail = response.json()
                alerts.append(self._format_notice(detail))

        return alerts

    def _format_notice(self, message: dict) -> str:
        headers = {
            item.get("name", "").lower(): item.get("value", "")
            for item in message.get("payload", {}).get("headers", [])
        }
        sender = self._decode_header(headers.get("from", "보낸 사람 없음"))
        subject = self._decode_header(headers.get("subject", "제목 없음"))
        return f"{subject} | 보낸 사람: {sender}"

    def _decode_header(self, value: str) -> str:
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="ignore"))
            else:
                decoded_parts.append(part)
        return self._clean_text("".join(decoded_parts))

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _keywords(self) -> list[str]:
        return [
            keyword.strip()
            for keyword in settings.gmail_important_keywords.split(",")
            if keyword.strip()
        ]

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

        with httpx.Client(timeout=20) as client:
            response = client.post(self.token_url, data=payload)
            response.raise_for_status()
            return response.json()

    def _authorize(self, credentials: dict) -> dict:
        server = HTTPServer(("localhost", 0), _GmailOAuthCallbackHandler)
        redirect_uri = f"http://localhost:{server.server_port}/"
        state = "daily-briefing-agent-gmail"

        params = {
            "client_id": credentials["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        webbrowser.open(f"{self.auth_url}?{urllib.parse.urlencode(params)}")
        server.handle_request()

        code = getattr(server, "auth_code", None)
        returned_state = getattr(server, "auth_state", None)
        if not code or returned_state != state:
            raise RuntimeError("Gmail 인증 코드를 받지 못했습니다.")

        payload = {
            "client_id": credentials["client_id"],
            "client_secret": credentials.get("client_secret", ""),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        with httpx.Client(timeout=20) as client:
            response = client.post(self.token_url, data=payload)
            response.raise_for_status()
            return response.json()


class _GmailOAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_url.query)

        self.server.auth_code = query.get("code", [None])[0]
        self.server.auth_state = query.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("Gmail 인증이 완료되었습니다. 이 창을 닫고 앱으로 돌아가세요.".encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        return
