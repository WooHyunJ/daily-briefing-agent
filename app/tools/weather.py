import httpx

from app.config import settings
from app.models.schemas import WeatherSnapshot


class WeatherTool:
    name = "get_weather"
    description = "지정한 도시의 현재 날씨를 가져옵니다."

    async def run(self, city: str = "Incheon") -> WeatherSnapshot:
        if not settings.use_weather_api or not settings.openweather_api_key:
            return WeatherSnapshot(summary="날씨 API 키가 없어 기본 날씨를 사용합니다.", temperature_c=15.0)

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": settings.openweather_api_key,
            "units": "metric",
            "lang": "kr",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            weather_main = data["weather"][0]["main"]
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]

            summary_text = weather_desc
            if weather_main in ["Rain", "Drizzle", "Thunderstorm"]:
                summary_text = f"현재 비가 내리고 있습니다. ({weather_desc})"

            return WeatherSnapshot(
                summary=summary_text,
                temperature_c=temp,
            )

        except Exception:
            return WeatherSnapshot(
                summary="날씨 API 연동에 실패해 기본 날씨를 사용합니다.",
                temperature_c=15.7,
            )
