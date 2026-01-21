import httpx
from typing import Any
from datetime import date

class NaverSportClient:
    BASE_URL = "https://api-gw.sports.naver.com"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Referer": "https://m.sports.naver.com",
        "Origin": "https://m.sports.naver.com",
    }

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def get_game_preview(self, game_id: str) -> dict[str, Any] | None:
        url = f"{self.BASE_URL}/schedule/games/{game_id}/preview"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.DEFAULT_HEADERS)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            return None
        except httpx.RequestError as e:
            return None

    def get_schedule(self, target_date: date | None = None) -> dict[str, Any] | None:
        if target_date is None:
            target_date = date.today()

        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/schedule/calendar"
        params = {
            "upperCategoryId": "kbaseball",
            "categoryIds": "kbo,kbaseballetc,premier12,apbc",
            "date": date_str,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.DEFAULT_HEADERS, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError:
            return None
