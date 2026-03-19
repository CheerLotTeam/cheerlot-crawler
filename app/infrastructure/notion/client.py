import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


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

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> dict:
        last_exception = None

        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method, url, headers=self._get_headers(), **kwargs
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                raise NotionClientError(
                    f"Notion API failed (HTTP {e.response.status_code}): {e.response.text}"
                ) from e
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
