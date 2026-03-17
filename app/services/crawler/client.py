import logging
from typing import Any
from datetime import date

import httpx

logger = logging.getLogger(__name__)


class NaverSportClient:
    BASE_URL = "https://api-gw.sports.naver.com"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Referer": "https://m.sports.naver.com",
        "Origin": "https://m.sports.naver.com",
    }

    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        self.timeout = timeout
        self._max_retries = max_retries

    def get_game_preview(self, game_id: str) -> dict[str, Any] | None:
        url = f"{self.BASE_URL}/schedule/games/{game_id}/preview"
        return self._request_with_retry("GET", url)

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

        return self._request_with_retry("GET", url, params=params)

    def _request_with_retry(self, method: str, url: str, **kwargs) -> dict[str, Any] | None:
        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, headers=self.DEFAULT_HEADERS, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning(f"API 요청 실패 ({attempt}/{self._max_retries}): {url} - {e}")
                if attempt == self._max_retries:
                    logger.error(f"API 요청 최종 실패: {url}")
                    return None
        return None
