import urllib.parse

import httpx

from app.config import settings
from app.models.schemas import UserProfile


class SubwayArrivalTool:
    name = "get_subway_arrivals"
    description = "서울 열린데이터광장 지하철 실시간 도착정보를 가져옵니다."

    base_url = "http://swopenAPI.seoul.go.kr/api/subway"

    async def run(self, profile: UserProfile) -> list[str] | None:
        if not settings.use_subway:
            return None

        station = profile.commute_station
        if not station:
            return ["출근역이 설정되지 않아 실시간 지하철 도착정보를 가져오지 않았습니다."]

        if not settings.seoul_subway_api_key:
            return ["서울 지하철 API 키가 없어 실시간 도착정보를 가져오지 않았습니다."]

        try:
            return await self._fetch_arrivals(profile)
        except Exception:
            return ["실시간 지하철 도착정보를 가져오지 못했습니다."]

    async def _fetch_arrivals(self, profile: UserProfile) -> list[str]:
        station = profile.commute_station or ""
        encoded_station = urllib.parse.quote(station)
        limit = max(settings.subway_arrival_limit, 1)
        url = (
            f"{self.base_url}/{settings.seoul_subway_api_key}/json/"
            f"realtimeStationArrival/0/{limit}/{encoded_station}"
        )

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        arrivals = data.get("realtimeArrivalList", [])
        filtered = self._filter_arrivals(arrivals, profile)
        if not filtered:
            return [f"{station}역 실시간 도착정보가 없습니다."]

        result = []
        for item in filtered[:limit]:
            line = item.get("subwayNm") or self._line_name(item.get("subwayId", ""))
            train_line = item.get("trainLineNm", "방면 정보 없음")
            arrival_message = item.get("arvlMsg2", "도착 정보 없음")
            previous_station = item.get("arvlMsg3", "")
            details = f"{line} {train_line}: {arrival_message}"
            if previous_station:
                details = f"{details} ({previous_station})"
            result.append(details)

        return result

    def _filter_arrivals(self, arrivals: list[dict], profile: UserProfile) -> list[dict]:
        filtered = arrivals
        if profile.commute_subway_line:
            target_line = profile.commute_subway_line.replace(" ", "")
            filtered = [
                item
                for item in filtered
                if target_line in self._line_name(item.get("subwayId", "")).replace(" ", "")
                or target_line in str(item.get("subwayNm", "")).replace(" ", "")
            ]

        if profile.commute_direction_keyword:
            keywords = [
                keyword.strip()
                for keyword in profile.commute_direction_keyword.split(",")
                if keyword.strip()
            ]
            filtered = [
                item
                for item in filtered
                if any(
                    keyword in str(item.get("trainLineNm", ""))
                    or keyword in str(item.get("bstatnNm", ""))
                    for keyword in keywords
                )
            ]

        return filtered

    def _line_name(self, subway_id: str) -> str:
        names = {
            "1001": "1호선",
            "1002": "2호선",
            "1003": "3호선",
            "1004": "4호선",
            "1005": "5호선",
            "1006": "6호선",
            "1007": "7호선",
            "1008": "8호선",
            "1009": "9호선",
            "1063": "경의중앙선",
            "1065": "공항철도",
            "1067": "경춘선",
            "1075": "수인분당선",
            "1077": "신분당선",
            "1092": "우이신설선",
            "1093": "서해선",
        }
        return names.get(str(subway_id), f"{subway_id}호선")
