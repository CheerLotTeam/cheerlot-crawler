import logging
import threading
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
MIN_REQUEST_INTERVAL = 0.34  # Notion 공개 API 한도 : 평균 3 req/s
RETRYABLE_STATUS = (429, 502, 503, 504)
DEFAULT_RETRY_AFTER = 1.0

# ponytail: 프로세스 전역 스로틀. 워커를 여러 개로 늘리면 Redis 토큰 버킷 필요
_throttle_lock = threading.Lock()
_last_request_at = 0.0


def _wait_for_slot() -> None:
    """Notion 한도는 integration 토큰 단위라 스케줄러 스레드 전체를 직렬화한다."""
    global _last_request_at

    with _throttle_lock:
        wait = MIN_REQUEST_INTERVAL - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()


class NotionClientError(Exception):
    pass


class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self._api_key = api_key or settings.notion_api_key
        self._timeout = timeout
        self._max_retries = max_retries

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _retry_after(self, response) -> float:
        try:
            return float(response.headers.get("Retry-After", DEFAULT_RETRY_AFTER))
        except (TypeError, ValueError):
            return DEFAULT_RETRY_AFTER

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> dict:
        last_exception = None

        for attempt in range(1, self._max_retries + 1):
            _wait_for_slot()
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method, url, headers=self._get_headers(), **kwargs
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code not in RETRYABLE_STATUS or attempt >= self._max_retries:
                    raise NotionClientError(
                        f"Notion API failed (HTTP {status_code}): {e.response.text}"
                    ) from e

                last_exception = e
                retry_after = self._retry_after(e.response)
                logger.warning(
                    f"Notion API 요청 제한 (HTTP {status_code}) "
                    f"({attempt}/{self._max_retries}): {url} - {retry_after}초 후 재시도"
                )
                time.sleep(retry_after)
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(
                    f"Notion API 요청 실패 ({attempt}/{self._max_retries}): {url} - {e}"
                )
                if attempt < self._max_retries:
                    time.sleep(1)

        raise NotionClientError(
            f"Notion API 최종 실패 ({self._max_retries}회 재시도 모두 실패): {url}"
        ) from last_exception

    def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
    ) -> list[dict]:
        body = {}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts

        url = f"{self.BASE_URL}/databases/{database_id}/query"
        result = self._request_with_retry("POST", url, json=body)
        return result.get("results", [])

    def create_page(self, database_id: str, properties: dict) -> dict:
        url = f"{self.BASE_URL}/pages"
        body = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        return self._request_with_retry("POST", url, json=body)

    def update_page(self, page_id: str, properties: dict) -> dict:
        url = f"{self.BASE_URL}/pages/{page_id}"
        return self._request_with_retry("PATCH", url, json={"properties": properties})

    def archive_page(self, page_id: str) -> dict:
        url = f"{self.BASE_URL}/pages/{page_id}"
        return self._request_with_retry("PATCH", url, json={"archived": True})
