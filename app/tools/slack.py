import httpx

from app.config import settings


class SlackNotifier:
    def is_enabled(self) -> bool:
        return settings.use_slack and bool(settings.slack_webhook_url)

    async def send(self, text: str) -> bool:
        if not self.is_enabled():
            return False

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                settings.slack_webhook_url,
                json={"text": text},
            )
            response.raise_for_status()

        return True
